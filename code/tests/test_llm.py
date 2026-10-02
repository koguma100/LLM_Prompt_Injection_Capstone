from unittest import mock

import pytest
import requests

from sanitizer import llm


def ok_response(text):
    r = mock.Mock(); r.raise_for_status = lambda: None; r.json = lambda: {"response": text}
    return r

refused = requests.exceptions.ConnectionError("Connection refused")


def test_retries_until_ollama_answers():
    with mock.patch("requests.post", side_effect=[refused, refused, ok_response("Yes.")]) as post, \
         mock.patch("time.sleep") as sleep:
        assert llm.local_llm_call("Is the sky blue?") == "Yes."
    assert post.call_count == 3
    assert [c.args[0] for c in sleep.call_args_list] == [1, 3]

def test_raises_instead_of_returning_a_fake_answer():
    # used to return False, which output validation then counted as a hijacked answer
    with mock.patch("requests.post", side_effect=refused) as post, mock.patch("time.sleep"):
        for call in (lambda: llm.local_llm_call("q"), lambda: llm.llm_validate("q", "a"), lambda: llm.is_prompt_injection("q")):
            with pytest.raises(llm.LLMUnavailable):
                call()
    assert post.call_count == 3 * (len(llm.RETRY_DELAYS) + 1)

def test_http_error_is_retried_too():
    bad = mock.Mock(); bad.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    with mock.patch("requests.post", side_effect=[bad, ok_response("1")]), mock.patch("time.sleep"):
        assert llm.llm_validate("q", "a") is True

def test_is_available():
    with mock.patch("requests.get", return_value=mock.Mock(ok=True)) as get:
        assert llm.is_available()
    assert get.call_args.args[0] == "http://localhost:11434/api/version"
    with mock.patch("requests.get", side_effect=refused):
        assert not llm.is_available()
