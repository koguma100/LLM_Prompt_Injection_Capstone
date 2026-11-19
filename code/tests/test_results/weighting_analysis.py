# Offline analysis of the cheap-detector weighted vote (config.DETECTOR_WEIGHTS / SKIP_LLM_THRESHOLD).
# Runs only the cheap detectors (regex + BoW), no LLM, so it covers every sample set quickly. From code/ run:
#     python tests/test_results/weighting_analysis.py
# Writes cheap_vote_summary.csv, threshold_sweep.csv, detector_hits.csv and per_sample_scores.csv next to this file.
import csv
import os
import sys
from collections import Counter

CODE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, CODE_DIR)

from sanitizer.config import DETECTOR_WEIGHTS, SKIP_LLM_THRESHOLD  # noqa: E402
from sanitizer.detection import Detect  # noqa: E402
from sanitizer.patterns import Patterns  # noqa: E402
from sanitizer.pipeline import cheap_vote  # noqa: E402
from evaluation.run_eval import bow_holdout  # noqa: E402
from evaluation.samples import SAMPLE_SETS, load_samples  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(CODE_DIR, "training", "injection_detector_datasetv2.csv")
THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]


def detect(text):
    d = Detect(text, Patterns)
    return {
        "instruction_overrides": d.regex_scanner(Patterns.INSTRUCTION_OVERRIDE_PATTERN),
        "authority_overrides": d.regex_scanner(Patterns.AUTHORITY_PATTERN),
        "outlier_clauses": [],  # disabled in pipeline.process_single
        "bow_malicious": d.BoW_malicious_scanner(),
    }


def sets():
    for name in SAMPLE_SETS:
        yield name, load_samples(name)
    if os.path.exists(V2):
        yield "datasetv2_bow_holdout", bow_holdout(load_samples(V2))


def main():
    summary, sweep, hits_rows, per_sample = [], [], [], []
    for name, samples in sets():
        scores, labels, hits = [], [], Counter()
        for i, (text, label) in enumerate(samples, 1):
            det = detect(text)
            score = cheap_vote(det)
            fired = [k for k, v in det.items() if v]
            hits.update((k, label) for k in fired)
            scores.append(score)
            labels.append(label)
            per_sample.append([name, i, label, score, int(score >= SKIP_LLM_THRESHOLD), int(bool(fired)), "+".join(fired)])

        n, mal = len(labels), sum(labels)
        for t in THRESHOLDS:
            skipped = [l for s, l in zip(scores, labels) if s >= t]
            tp = sum(skipped)
            sweep.append([name, t, n, len(skipped), f"{len(skipped) / n:.3f}",
                          tp, len(skipped) - tp,
                          f"{tp / len(skipped):.3f}" if skipped else "",
                          f"{tp / mal:.3f}" if mal else "",
                          f"{(len(skipped) - tp) / (n - mal):.3f}" if n - mal else ""])
        any_det = [l for s, l in zip(scores, labels) if s > 0]
        skipped = [l for s, l in zip(scores, labels) if s >= SKIP_LLM_THRESHOLD]
        summary.append([name, n, mal, n - mal,
                        len(any_det), sum(any_det),  # flagged by any cheap detector / of those malicious
                        len(skipped), sum(skipped), len(skipped) - sum(skipped),
                        f"{len(skipped) / n:.3f}",
                        f"{4 * len(skipped) / (4 * n):.3f}",  # share of LLM calls saved (4 per sample)
                        dict(Counter(scores))])
        for k in DETECTOR_WEIGHTS:
            hits_rows.append([name, k, DETECTOR_WEIGHTS[k], hits[(k, 1)], mal, hits[(k, 0)], n - mal])
        print(f"{name:28} n={n:5}  skip={len(skipped):5} ({len(skipped) / n:.1%})  skipped benign={len(skipped) - sum(skipped)}")

    def write(fname, header, rows):
        with open(os.path.join(OUT_DIR, fname), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write("cheap_vote_summary.csv",
          ["set", "samples", "malicious", "benign", "flagged_any", "flagged_any_malicious",
           f"skipped@{SKIP_LLM_THRESHOLD}", "skipped_malicious", "skipped_benign", "skip_rate", "llm_calls_saved",
           "score_distribution"], summary)
    write("threshold_sweep.csv",
          ["set", "threshold", "samples", "skipped", "skip_rate", "skipped_malicious", "skipped_benign",
           "skip_precision", "share_of_malicious_skipped", "share_of_benign_skipped"], sweep)
    write("detector_hits.csv",
          ["set", "detector", "weight", "hits_on_malicious", "malicious", "hits_on_benign", "benign"], hits_rows)
    write("per_sample_scores.csv",
          ["set", "sample", "label", "cheap_score", "skipped", "any_detection", "detectors_fired"], per_sample)


if __name__ == "__main__":
    main()
