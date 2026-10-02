import csv
from unittest import mock

import pytest

from evaluation import run_eval
from sanitizer.llm import LLMUnavailable
from sanitizer.pipeline import Result

DATA = [(f"sample text {i}", i % 2) for i in range(1, 7)]


def fake_result(prompt, text, patterns=None):
    return Result(prompt=prompt, original=text, sanitized=text, outlier_clauses=[], instruction_overrides=[],
                  authority_overrides=[], bow_malicious=["x"] if text.endswith(("1", "3", "5")) else [],
                  standalone=[], embedded=[], unsanitized_output="a", sanitized_output="b",
                  unsanitized_valid=True, sanitized_valid=True)

def run(tmp_path, side_effect, **kwargs):
    with mock.patch.object(run_eval, "process_single", side_effect=side_effect) as ps, \
         mock.patch("time.sleep"):
        preds = run_eval.process_predict_batch("q", DATA, out_dir=str(tmp_path), quiet=True, **kwargs)
    return preds, ps

def rows(tmp_path):
    with open(tmp_path / "predictions.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_full_run_writes_all_outputs(tmp_path):
    preds, _ = run(tmp_path, fake_result)
    assert preds == [1, 0, 1, 0, 1, 0]
    assert len(rows(tmp_path)) == 6
    assert "Accuracy:  1.0000" in (tmp_path / "performance_stats.txt").read_text()
    assert (tmp_path / "confusion_matrix.png").exists()

def test_waits_for_ollama_and_retries_the_sample(tmp_path, capsys):
    calls = iter([fake_result, fake_result, LLMUnavailable("down"), LLMUnavailable("down")] + [fake_result] * 10)
    def flaky(*args):
        step = next(calls)
        if isinstance(step, Exception):
            raise step
        return step(*args)
    with mock.patch.object(run_eval, "is_available", return_value=True):
        preds, ps = run(tmp_path, flaky)
    assert preds == [1, 0, 1, 0, 1, 0]                       # nothing recorded during the outage
    assert [r["sample"] for r in rows(tmp_path)] == ["1", "2", "3", "4", "5", "6"]
    assert "Waiting up to 10 min" in capsys.readouterr().out

def test_stops_with_stats_when_ollama_stays_down(tmp_path, capsys):
    calls = iter([fake_result, fake_result])
    def down_after_two(*args):
        step = next(calls, None)
        if step is None:
            raise LLMUnavailable("down")
        return step(*args)
    with mock.patch.object(run_eval, "is_available", return_value=False):
        preds, _ = run(tmp_path, down_after_two, max_wait=0)
    assert preds == [1, 0]
    assert len(rows(tmp_path)) == 2
    assert (tmp_path / "performance_stats.txt").exists()
    assert "stopped after 2 of 6 samples" in capsys.readouterr().out

def test_ctrl_c_keeps_finished_samples_and_writes_stats(tmp_path, capsys):
    calls = iter([fake_result, fake_result, fake_result])
    def interrupted(*args):
        step = next(calls, None)
        if step is None:
            raise KeyboardInterrupt
        return step(*args)
    preds, _ = run(tmp_path, interrupted)
    assert preds == [1, 0, 1]
    assert (tmp_path / "confusion_matrix.png").exists()
    assert "Interrupted: stopped after 3 of 6 samples" in capsys.readouterr().out

def test_resume_continues_after_finished_samples(tmp_path):
    calls = iter([fake_result, fake_result])
    def interrupted(*args):
        step = next(calls, None)
        if step is None:
            raise KeyboardInterrupt
        return step(*args)
    run(tmp_path, interrupted)
    preds, ps = run(tmp_path, fake_result, resume=True)
    assert preds == [1, 0, 1, 0, 1, 0]
    assert [c.args[1] for c in ps.call_args_list] == [t for t, _ in DATA[2:]]   # only the unfinished samples ran
    assert [r["sample"] for r in rows(tmp_path)] == ["1", "2", "3", "4", "5", "6"]

def test_resume_refuses_a_different_run(tmp_path):
    run(tmp_path, fake_result)
    other = [(f"other text {i}", 0) for i in range(6)]
    with mock.patch.object(run_eval, "process_single", side_effect=fake_result), pytest.raises(run_eval.ResumeMismatch):
        run_eval.process_predict_batch("q", other, out_dir=str(tmp_path), quiet=True, resume=True)

def test_without_resume_starts_over(tmp_path):
    run(tmp_path, fake_result)
    preds, ps = run(tmp_path, fake_result)
    assert ps.call_count == 6 and len(rows(tmp_path)) == 6
