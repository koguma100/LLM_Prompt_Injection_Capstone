# Runs every cheap detector over every sample set and records what each one found, including how confident the
# learned models were. No LLM. Output feeds fit_weights.py. From code/ run:
#     python tests/test_results/detector_features.py                     # every set
#     python tests/test_results/detector_features.py --sets datasetv2_holdout resumes_half_pi --llm-subset hugging_face_prompts
# Writes detector_features.csv next to this file, adding one set at a time (sets already in it are skipped).
import argparse
import csv
import os
import re
import sys

CODE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, CODE_DIR)

from sanitizer.detection import Detect, rf  # noqa: E402
from sanitizer.patterns import Patterns  # noqa: E402
from evaluation.run_eval import bow_holdout  # noqa: E402
from evaluation.samples import SAMPLE_SETS, load_samples  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "detector_features.csv")
V2 = os.path.join(CODE_DIR, "training", "injection_detector_datasetv2.csv")


def sentences(text):
    # Same splitting as rf_scan
    return re.split(r'(?<=[.!?])\s+', text)


def features(text):
    d = Detect(text, Patterns)
    sents = sentences(text)
    rf_p = rf.load_model(rf.MALICIOUS_MODEL).predict_proba(sents)[:, 1]
    row = {
        "instruction": int(bool(d.regex_scanner(Patterns.INSTRUCTION_OVERRIDE_PATTERN))),
        "authority": int(bool(d.regex_scanner(Patterns.AUTHORITY_PATTERN))),
        "sentences": len(sents),
        "rf_hits": int((rf_p >= 0.5).sum()),
        "rf_max": round(float(rf_p.max()), 4),
    }
    return row


ALL_SETS = [*SAMPLE_SETS, "datasetv2_holdout"]
LLM_EVAL = os.path.join(os.path.dirname(OUT), "llm_validator_eval.csv")


def load(name):
    return bow_holdout(load_samples(V2)) if name == "datasetv2_holdout" else load_samples(name)


# Sample numbers of a set that llm_validator_eval.csv covers
def llm_samples(name):
    with open(LLM_EVAL, newline="") as f:
        return {int(r["sample"]) for r in csv.DictReader(f) if r["set"] == name}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sets", nargs="*", default=ALL_SETS, help="sets to score in full")
    parser.add_argument("--llm-subset", nargs="*", default=[],
                        help="sets to score only on the samples in llm_validator_eval.csv")
    args = parser.parse_args()

    done = set()
    if os.path.exists(OUT):
        with open(OUT, newline="") as f:
            done = {r["set"] for r in csv.DictReader(f)}
    jobs = [(name, None) for name in args.sets] + [(name, llm_samples(name)) for name in args.llm_subset]
    for name, keep in jobs:
        if name in done:
            print(f"{name:24} already scored")
            continue
        rows = [{"set": name, "sample": i, "label": label, **features(text)}
                for i, (text, label) in enumerate(load(name), 1) if keep is None or i in keep]
        new = not os.path.exists(OUT)
        with open(OUT, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"{name:24} {len(rows)} samples", flush=True)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
