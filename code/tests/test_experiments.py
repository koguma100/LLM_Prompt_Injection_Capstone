import re
from unittest import mock

import pytest

from sanitizer.llm import LLMUnavailable
from sanitizer.pipeline import Result
from webapp import create_app, experiments, routes

FORM = {"prompt": "Summarize.", "data": "Some data.", "mit_regex": "on", "compare_baseline": "on"}


def fake_result(prompt="Summarize.", data="Some data."):
    return Result(prompt=prompt, original=data, sanitized="[REDACTED]", outlier_clauses=[], instruction_overrides=["x"],
                  authority_overrides=[], bow_malicious=[], standalone=["x"], embedded=[],
                  unsanitized_output="unsanitized answer", sanitized_output="sanitized answer",
                  unsanitized_valid=False, sanitized_valid=True)


@pytest.fixture
def app():
    with mock.patch.object(routes, "process_single", side_effect=lambda p, d: fake_result(p, d)):
        yield create_app()


@pytest.fixture
def client(app):
    return app.test_client()


def hidden(html, name):
    return re.search(rf'name="{name}" value="([^"]*)"', html).group(1)


def run(client, **changes):
    html = client.post("/", data={**FORM, **changes}).data.decode()
    return html, hidden(html, "run_id")


def saved(app):
    with app.app_context():
        return experiments.list_experiments()


def test_run_is_not_listed_until_saved(app, client):
    _, run_id = run(client)
    assert run_id
    assert saved(app) == []
    assert "No saved experiments yet" in client.get("/experiments").data.decode()


def test_save_keeps_name_inputs_settings_and_results(app, client):
    _, run_id = run(client)
    resp = client.post("/experiments/save", data={**FORM, "experiment_name": "Override test", "run_id": run_id})
    assert resp.status_code == 302

    [exp] = saved(app)
    assert resp.headers["Location"].endswith(f"/experiments/{exp['id']}")
    assert exp["name"] == "Override test"
    assert (exp["prompt"], exp["data"]) == ("Summarize.", "Some data.")
    assert exp["settings"] == {**{k: False for k in routes.DEFAULT_SETTINGS}, "mit_regex": True, "compare_baseline": True}
    assert exp["result"] == fake_result()

    html = client.get(f"/experiments/{exp['id']}").data.decode()
    for shown in ("Override test", "Saved result", "sanitized answer", "unsanitized answer", "Some data."):
        assert shown in html
    # the saved toggle states are restored, not the defaults
    assert re.search(r'name="mit_regex" checked', html)
    assert not re.search(r'name="mit_hardening" checked', html)
    assert "Override test" in client.get("/experiments").data.decode()


def test_saving_the_run_names_it_instead_of_copying_it(app, client):
    _, run_id = run(client)
    client.post("/experiments/save", data={**FORM, "experiment_name": "A", "run_id": run_id})
    assert [e["id"] for e in saved(app)] == [int(run_id)]


def test_inputs_changed_after_the_run_save_as_a_draft(app, client):
    _, run_id = run(client)
    client.post("/experiments/save", data={**FORM, "data": "Edited data.", "experiment_name": "Edited", "run_id": run_id})
    [exp] = saved(app)
    assert exp["result"] is None
    assert exp["data"] == "Edited data."
    assert "Draft" in client.get("/experiments").data.decode()


def test_toggle_changed_after_the_run_saves_as_a_draft(app, client):
    _, run_id = run(client)
    client.post("/experiments/save", data={**FORM, "mit_sanitization": "on", "experiment_name": "x", "run_id": run_id})
    assert saved(app)[0]["result"] is None


def test_textarea_newlines_still_match_the_run(app, client):
    _, run_id = run(client, data="line one\r\nline two")
    client.post("/experiments/save", data={**FORM, "data": "line one\nline two", "experiment_name": "x", "run_id": run_id})
    assert saved(app)[0]["result"] is not None


def test_save_without_running_is_a_draft(app, client):
    client.post("/experiments/save", data={**FORM, "experiment_name": "Just inputs"})
    [exp] = saved(app)
    assert exp["name"] == "Just inputs" and exp["result"] is None


def test_blank_name_gets_a_default(app, client):
    client.post("/experiments/save", data={**FORM, "experiment_name": "   "})
    assert saved(app)[0]["name"] == "Untitled experiment"


def test_rerun_and_save_updates_the_loaded_experiment(app, client):
    client.post("/experiments/save", data={**FORM, "experiment_name": "Mine"})
    [exp] = saved(app)

    html, run_id = run(client, data="New data.", experiment_id=str(exp["id"]), experiment_name="Mine v2")
    assert hidden(html, "experiment_id") == str(exp["id"])
    client.post("/experiments/save", data={**FORM, "data": "New data.", "experiment_name": "Mine v2",
                                           "run_id": run_id, "experiment_id": str(exp["id"])})
    [updated] = saved(app)
    assert updated["id"] == exp["id"]
    assert updated["name"] == "Mine v2"
    assert updated["result"] == fake_result(data="New data.")


def test_resaving_unchanged_experiment_keeps_its_results(app, client):
    _, run_id = run(client)
    client.post("/experiments/save", data={**FORM, "experiment_name": "Keep", "run_id": run_id})
    [exp] = saved(app)
    client.post("/experiments/save", data={**FORM, "experiment_name": "Renamed", "experiment_id": str(exp["id"])})
    [again] = saved(app)
    assert again["name"] == "Renamed" and again["result"] == fake_result()


def test_cannot_save_into_an_unsaved_run_by_id(app, client):
    _, run_id = run(client)
    # an unsaved run id passed as experiment_id is not treated as a saved experiment to update
    client.post("/experiments/save", data={**FORM, "data": "Other.", "experiment_name": "x", "experiment_id": run_id})
    [exp] = saved(app)
    assert exp["id"] != int(run_id)


def test_delete(app, client):
    client.post("/experiments/save", data={**FORM, "experiment_name": "Gone"})
    [exp] = saved(app)
    resp = client.post(f"/experiments/{exp['id']}/delete")
    assert resp.status_code == 302
    assert saved(app) == []
    assert client.get(f"/experiments/{exp['id']}").status_code == 404


def test_unsaved_runs_are_not_viewable_or_deletable(app, client):
    _, run_id = run(client)
    assert client.get(f"/experiments/{run_id}").status_code == 404
    client.post(f"/experiments/{run_id}/delete")
    with app.app_context():
        assert experiments._row(int(run_id)) is not None


def test_old_unsaved_runs_are_pruned(app, client):
    _, old_id = run(client)
    with app.app_context():
        db = experiments.get_db()
        db.execute("UPDATE experiments SET created_at = '2000-01-01T00:00:00+00:00' WHERE id = ?", (old_id,))
        db.commit()
    run(client)
    with app.app_context():
        assert experiments._row(int(old_id)) is None


def test_failed_run_is_not_recorded(client):
    with mock.patch.object(routes, "process_single", side_effect=LLMUnavailable("down")):
        html = client.post("/", data=FORM).data.decode()
    assert "Could not reach the LLM" in html
    assert hidden(html, "run_id") == ""


def test_sidebar_counts_saved_experiments(client):
    assert '<span class="nav-count">00</span>' in client.get("/").data.decode()
    client.post("/experiments/save", data={**FORM, "experiment_name": "One"})
    assert '<span class="nav-count">01</span>' in client.get("/").data.decode()


def test_names_are_escaped(app, client):
    client.post("/experiments/save", data={**FORM, "experiment_name": "<script>alert(1)</script>"})
    html = client.get("/experiments").data.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_get_shows_default_toggles(client):
    html = client.get("/").data.decode()
    for name, on in routes.DEFAULT_SETTINGS.items():
        assert bool(re.search(rf'name="{name}" checked', html)) == on


def test_saved_result_survives_a_new_field_in_result(app, client):
    _, run_id = run(client)
    client.post("/experiments/save", data={**FORM, "experiment_name": "x", "run_id": run_id})
    with app.app_context():
        db = experiments.get_db()
        db.execute("UPDATE experiments SET result = json_remove(result, '$.bow_malicious', '$.sanitized_valid')")
        db.commit()
        result = experiments.list_experiments()[0]["result"]
        assert result.bow_malicious == [] and result.sanitized_valid is False
    # bow_malicious feeds Result.detections, which both pages use
    assert client.get("/experiments").status_code == 200
    assert client.get(f"/experiments/{run_id}").status_code == 200


@pytest.mark.parametrize("big", ["9223372036854775808", "99999999999999999999999999"])
def test_ids_too_large_for_sqlite_are_not_found(client, big):
    assert client.get(f"/experiments/{big}").status_code == 404
    assert client.post(f"/experiments/{big}/delete").status_code == 302
    assert client.post("/experiments/save", data={**FORM, "experiment_name": "x", "run_id": big,
                                                  "experiment_id": big}).status_code == 302
    assert client.post("/", data={**FORM, "experiment_id": big}).status_code == 200


def test_saving_an_expired_run_says_so(app, client):
    _, run_id = run(client)
    with app.app_context():
        db = experiments.get_db()
        db.execute("DELETE FROM experiments WHERE id = ?", (run_id,))
        db.commit()
    resp = client.post("/experiments/save", data={**FORM, "experiment_name": "Late", "run_id": run_id})
    assert resp.headers["Location"].endswith("?expired=1")
    html = client.get(resp.headers["Location"]).data.decode()
    assert "Saved without results" in html and "had expired" in html
    assert "Saved without results" not in client.get(resp.headers["Location"].split("?")[0]).data.decode()


@pytest.mark.parametrize("headers, allowed", [
    ({"Sec-Fetch-Site": "cross-site"}, False),
    ({"Sec-Fetch-Site": "same-site"}, False),
    ({"Sec-Fetch-Site": "same-origin"}, True),
    ({"Sec-Fetch-Site": "none"}, True),
    ({"Origin": "https://evil.example"}, False),
    ({"Origin": "http://localhost"}, True),
    ({}, True),
])
def test_cross_site_posts_are_rejected(app, client, headers, allowed):
    client.post("/experiments/save", data={**FORM, "experiment_name": "Keep"})
    [exp] = saved(app)
    resp = client.post(f"/experiments/{exp['id']}/delete", headers=headers)
    assert (resp.status_code == 302) == allowed
    assert (saved(app) == []) == allowed


def test_enter_in_a_field_runs_instead_of_saving(client):
    html = client.get("/").data.decode()
    # the browser's default button is the first submit button owned by the form; it must not be Save
    first = re.search(r'<button type="submit"[^>]*form="exp-form"[^>]*>', html).group(0)
    assert "formaction" not in first and "hidden" in first


def test_technique_guide(client):
    html = client.get("/guide").data.decode()
    for technique in ("Text deobfuscation", "Regex injection detection", "Bag-of-words classifier", "Sanitization",
                      "Prompt hardening template", "Output validation"):
        assert technique in html
    assert 'class="topbar-link on" href="/guide"' in html
    assert '<a class="topbar-link " href="/guide"' in client.get("/").data.decode()
