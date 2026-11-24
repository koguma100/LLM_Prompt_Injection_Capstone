# Measures how well the LLM output validator separates injections from benign data, so its vote can be weighed
# against the cheap detectors. For each sample it does what process_single does on the sanitized path: redact
# everything the cheap detectors flagged, answer the prompt with the sanitized data, and validate the answer.
# Needs Ollama. From code/ run:
#     python tests/test_results/llm_validator_eval.py
# Appends to llm_validator_eval.csv next to this file (rerun to resume where it stopped).
import csv
import os
import random
import sys

CODE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, CODE_DIR)

from nltk.tokenize import sent_tokenize  # noqa: E402

from sanitizer.detection import Detect  # noqa: E402
from sanitizer.llm import llm_validate, local_llm_call  # noqa: E402
from sanitizer.patterns import Patterns  # noqa: E402
from sanitizer.sanitize import Sanitize  # noqa: E402
from evaluation.run_eval import DEFAULT_PROMPT, bow_holdout  # noqa: E402
from evaluation.samples import load_samples  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_validator_eval.csv")
V2 = os.path.join(CODE_DIR, "training", "injection_detector_datasetv2.csv")


def subset(samples, n, seed=0):
    idx = sorted(random.Random(seed).sample(range(len(samples)), min(n, len(samples))))
    return [(i + 1, samples[i]) for i in idx]


# (set name, prompt, [(sample number, (text, label))])
PLAN = [
    ("resumes_half_pi", DEFAULT_PROMPT, subset(load_samples("resumes_half_pi"), 50)),
    ("resumes_all_benign", DEFAULT_PROMPT, subset(load_samples("resumes_all_benign"), 50)),
    ("datasetv2_holdout", "Summarize this text.", subset(bow_holdout(load_samples(V2)), 60)),
    ("hugging_face_prompts", "Summarize this text.", subset(load_samples("hugging_face_prompts"), 40)),
]


def sanitize(data):
    d = Detect(data, Patterns)
    found = (d.regex_scanner(Patterns.INSTRUCTION_OVERRIDE_PATTERN) + d.regex_scanner(Patterns.AUTHORITY_PATTERN)
             + d.RF_malicious_scanner())
    sentences = sent_tokenize(data)
    embedded = [x for x in found if any(x.lower() in s.lower() and not s.strip().lower().startswith(x.lower())
                                        for s in sentences)]
    s = Sanitize(data)
    if [x for x in found if x not in embedded]:
        s.redact_sentences([x for x in found if x not in embedded])
    if embedded:
        s.redact_injection_clause(embedded)
    return s.data


def main():
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            done = {(r["set"], int(r["sample"])) for r in csv.DictReader(f)}
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["set", "sample", "label", "sanitized_valid", "answer"])
        for name, prompt, samples in PLAN:
            for num, (text, label) in samples:
                if (name, num) in done:
                    continue
                answer = local_llm_call(f"{prompt}\n\nResume:\n{sanitize(text)}")
                valid = llm_validate(prompt, answer)
                w.writerow([name, num, label, int(valid), answer.strip().replace("\n", " ")[:300]])
                f.flush()
                print(name, num, label, valid, flush=True)


if __name__ == "__main__":
    main()
