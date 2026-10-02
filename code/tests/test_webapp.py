import os
import runpy
from unittest import mock

import pytest
from flask import Flask

from webapp import create_app, routes


@pytest.fixture
def client():
    fake_result = (1, "original", "[REDACTED]", "unsanitized answer", "sanitized answer")
    with mock.patch.object(routes, "process_single", return_value=fake_result):
        yield create_app().test_client()


def test_requests_do_not_change_the_shared_template(client):
    before = routes.prompt_template
    client.post("/", data={"prompt": "first prompt", "data": "first data"})
    client.post("/", data={"prompt": "second prompt", "data": "second data"})
    assert routes.prompt_template is before
    assert not any("first" in part or "second" in part for part in routes.prompt_template)

def test_harden_prompt_places_prompt_and_data_inside_tags():
    hardened = routes.harden_prompt("Is this person qualified?", "Resume text")
    assert hardened.index("[QUESTION] Is this person qualified? [/QUESTION]") < hardened.index("[CONTEXT] Resume text [/CONTEXT]")

def test_post_renders_report(client):
    html = client.post("/", data={"prompt": "Summarize.", "data": "Some data."}).data.decode()
    assert "[REDACTED]" in html


@pytest.mark.parametrize("env, expected", [({}, False), ({"FLASK_DEBUG": "1"}, True), ({"FLASK_DEBUG": "0"}, False)])
def test_debug_mode_comes_from_environment(env, expected):
    with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(Flask, "run") as run:
        if "FLASK_DEBUG" not in env:
            os.environ.pop("FLASK_DEBUG", None)
        runpy.run_module("webapp", run_name="__main__")
    run.assert_called_once_with(debug=expected)
