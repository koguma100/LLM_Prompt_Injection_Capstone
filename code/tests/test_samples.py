import pytest

from evaluation.samples import SAMPLE_SETS, load_samples

EXPECTED = {"embedded_pi_tests": 15, "hugging_face_prompts": 1000, "imperative_tests": 25,
            "resumes_all_benign": 50, "resumes_half_pi": 50, "simple_prompts": 4}


def test_all_sample_sets_are_found():
    assert SAMPLE_SETS == sorted(EXPECTED)

@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_sample_set_loads(name):
    samples = load_samples(name)
    assert len(samples) == EXPECTED[name]
    assert all(isinstance(text, str) and text for text, _ in samples)
    assert {label for _, label in samples} <= {0, 1}

def test_multiline_text_survives_csv():
    assert any("\n" in text for text, _ in load_samples("hugging_face_prompts"))
