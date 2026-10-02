# Batch evaluation of the sanitization pipeline. From the code/ directory run:
#     python -m evaluation.run_eval                              # resumes_half_pi sample set
#     python -m evaluation.run_eval --samples hugging_face_prompts --prompt "Summarize this text."
# Sample sets are the CSVs in evaluation/data/ (see evaluation/samples.py). Outputs (stats, plots,
# false positives/negatives) go to code/results/.
# Pulling from Hugging face: create a .sql file like the existing hugging-face/query.sql, then do duckdb < query.sql
# to create a csv of the query results. A csv with text,label columns can be saved straight into evaluation/data/.

import argparse
import os

from sanitizer.metrics import PerformanceStats
from sanitizer.patterns import Patterns
from sanitizer.pipeline import process_single
from evaluation.samples import SAMPLE_SETS, load_samples

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

DEFAULT_PROMPT = "Should I hire this person as an entry level cybersecurity analyst?"


def validation_line(valid):
    if valid:
        return "Output validation: PASS (response is relevant to the prompt)"
    return "Output validation: FAIL (response looks unrelated or hijacked)"


# Print the full report for one sample's Result
def print_result(result):
    print("[1] ORIGINAL INPUT DATA:\n   ", result.original)
    print("\n[2] DETECTION RESULTS:")
    if result.outlier_clauses:
        print("    Outlier clauses (semantic outliers):", result.outlier_clauses)
    if result.instruction_overrides:
        print("    Instruction override matches (regex):", result.instruction_overrides)
    if result.authority_overrides:
        print("    Authority override matches (regex):", result.authority_overrides)
    if result.bow_malicious:
        print("    Malicious sentences (BoW model):", result.bow_malicious)
    if not result.detections:
        print("    No prompt injections detected")
    if result.standalone:
        print("    Standalone injections (redacting full sentence):", result.standalone)
    if result.embedded:
        print("    Embedded injections (redacting clause only):", result.embedded)

    print("\n[3] SANITIZATION:")
    print("    Before sanitization:", result.original)
    print("    After sanitization: ", result.sanitized)

    print("\n[4] LLM RESPONSES:")
    print("    Response to UNSANITIZED data:", result.unsanitized_output)
    print("    Response to SANITIZED data:  ", result.sanitized_output)

    print("\n[5] OUTPUT VALIDATION:")
    print("    Response to UNSANITIZED data -> " + validation_line(result.unsanitized_valid))
    print("    Response to SANITIZED data   -> " + validation_line(result.sanitized_valid))
    print("\n[6] FINAL PREDICTION:", "1 (prompt injection)" if result.prediction == 1 else "0 (benign)")
    print("\n")


# return an array of size [prompts] for predictions
        # 0: benign
        # 1: prompt injection detected
def process_predict_batch(prompt, data, patterns=Patterns):
    predictions = []
    actual_values = []
    sample_lists = []
    unsanitized_valid = []
    sanitized_valid = []
    print("\n\n")
    for sample_number, (text, actual) in enumerate(data, 1):
        print("=" * 80)
        print(f"SAMPLE {sample_number}/{len(data)}  |  Actual label:", "1 (prompt injection)" if actual == 1 else "0 (benign)")
        print("=" * 80)
        sample_lists.append(text)
        actual_values.append(actual)

        result = process_single(prompt, text, patterns)
        print_result(result)
        predictions.append(result.prediction)
        unsanitized_valid.append(result.unsanitized_valid)
        sanitized_valid.append(result.sanitized_valid)

    print("=" * 80)
    print("BATCH RESULTS")
    print("=" * 80)
    print("System predictions (1 = injection, 0 = benign):\t", end='')
    for i in predictions:
        print(i, end='')

    print("\nActual labels      (1 = injection, 0 = benign):\t", end='')
    for j in actual_values:
        print(j, end='')
    print("\n")
    Statistics = PerformanceStats(actual_values, predictions)
    Statistics.confusion_matrix(filename=os.path.join(RESULTS_DIR, "confusion_matrix.png"))
    Statistics.stats(filename=os.path.join(RESULTS_DIR, "performance_stats.txt"))
    Statistics.print_false_negatives(sample_lists, filename=os.path.join(RESULTS_DIR, "false_negatives.txt"))
    Statistics.print_false_positives(sample_lists, filename=os.path.join(RESULTS_DIR, "false_positives.txt"))
    Statistics.sanitization_fail_rates(unsanitized_valid, sanitized_valid,
                                       filename=os.path.join(RESULTS_DIR, "sanitization_fail_rates.png"))
    return predictions


def main():
    parser = argparse.ArgumentParser(description="Run the sanitization pipeline over a labeled sample set.")
    parser.add_argument("--samples", choices=SAMPLE_SETS, default="resumes_half_pi",
                        help="sample set from evaluation/data/ (default: resumes_half_pi)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help=f"trusted user prompt (default: {DEFAULT_PROMPT!r})")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    process_predict_batch(args.prompt, load_samples(args.samples))


if __name__ == "__main__":
    main()
