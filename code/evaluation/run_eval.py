# Batch evaluation of the sanitization pipeline. From the code/ directory run:
#     python -m evaluation.run_eval                              # resumes_half_pi sample set
#     python -m evaluation.run_eval --samples hugging_face_prompts --prompt "Summarize this text."
#     python -m evaluation.run_eval --samples training/injection_detector_datasetv2.csv --holdout --limit 500 --quiet
# --samples takes a sample set name (the CSVs in evaluation/data/) or the path to any CSV with text and label
# columns. Each sample takes about 10 seconds (four LLM calls), so use --limit on large files.
# Outputs (stats, plots, false positives/negatives, per-sample predictions) go to code/results/<sample set>/.
# Pulling from Hugging face: create a .sql file like the existing hugging-face/query.sql, then do duckdb < query.sql
# to create a csv of the query results. A csv with text,label columns can be saved straight into evaluation/data/.

import argparse
import csv
import os
import random
import time

from sklearn.model_selection import train_test_split

from sanitizer.llm import LLMUnavailable, is_available
from sanitizer.metrics import PerformanceStats
from sanitizer.patterns import Patterns
from sanitizer.pipeline import process_single
from evaluation.samples import SAMPLE_SETS, load_samples, sample_path

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

DEFAULT_PROMPT = "Should I hire this person as an entry level cybersecurity analyst?"

# The train/test split training/train_bow.py uses, so --holdout keeps only the rows the BoW models never saw
BOW_TEST_SIZE = .2
BOW_SPLIT_SEED = 10


# The rows train_bow.py held out as its test set (assumes the BoW models were trained on this same file)
def bow_holdout(samples):
    _, test_indices = train_test_split(range(len(samples)), test_size=BOW_TEST_SIZE, random_state=BOW_SPLIT_SEED)
    return [samples[i] for i in sorted(test_indices)]


# A reproducible random subset of n samples, kept in file order
def random_subset(samples, n, seed):
    if n >= len(samples):
        return samples
    return [samples[i] for i in sorted(random.Random(seed).sample(range(len(samples)), n))]


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
# predictions.csv doesn't belong to the samples being resumed
class ResumeMismatch(Exception):
    pass


PREDICTIONS_HEADER = ["sample", "label", "prediction", "unsanitized_valid", "sanitized_valid", "detections", "text", "sanitized"]


# Rows of a previous run's predictions.csv, checked against this run's samples so --resume can't mix up runs
def load_previous_predictions(path, data):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        number = int(row["sample"])
        if number > len(data) or data[number - 1] != (row["text"], int(row["label"])):
            raise ResumeMismatch(f"{path} is from a different run (sample {number} doesn't match); "
                             "use the same --samples/--holdout/--limit/--seed, or rerun without --resume")
    return rows


# Run process_single, and if Ollama is down, wait up to max_wait minutes for it to come back and try again
def process_with_wait(prompt, text, patterns, max_wait):
    deadline = None
    while True:
        try:
            return process_single(prompt, text, patterns)
        except LLMUnavailable as e:
            if deadline is None:
                deadline = time.time() + max_wait * 60
                print(f"Ollama is unreachable ({e}). Waiting up to {max_wait} min for it to come back...", flush=True)
            if time.time() > deadline:
                raise
            time.sleep(15)
            if is_available():
                print("Ollama is back; retrying the sample.", flush=True)


# quiet: print one progress line per sample instead of its full report
# resume: keep the samples already in out_dir/predictions.csv and continue after them
# max_wait: minutes to wait for Ollama to come back if it goes down mid-run
def process_predict_batch(prompt, data, patterns=Patterns, out_dir=None, quiet=False, resume=False, max_wait=10):
    out_dir = out_dir or RESULTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    predictions = []
    actual_values = []
    sample_lists = []
    unsanitized_valid = []
    sanitized_valid = []
    print("\n\n")

    # Per-sample results, written as the run goes so an interrupted run keeps what it finished
    predictions_path = os.path.join(out_dir, "predictions.csv")
    previous = load_previous_predictions(predictions_path, data) if resume else []
    for row in previous:
        actual_values.append(int(row["label"]))
        sample_lists.append(row["text"])
        predictions.append(int(row["prediction"]))
        unsanitized_valid.append(row["unsanitized_valid"] == "True")
        sanitized_valid.append(row["sanitized_valid"] == "True")
    if previous:
        print(f"Resuming: {len(previous)} of {len(data)} samples already done in {predictions_path}")
    predictions_file = open(predictions_path, "a" if previous else "w", newline="", encoding="utf-8")
    writer = csv.writer(predictions_file, lineterminator="\n")
    if not previous:
        writer.writerow(PREDICTIONS_HEADER)

    start = time.time()
    stopped = None
    for sample_number, (text, actual) in enumerate(data, 1):
        if sample_number <= len(previous):
            continue
        if not quiet:
            print("=" * 80)
            print(f"SAMPLE {sample_number}/{len(data)}  |  Actual label:", "1 (prompt injection)" if actual == 1 else "0 (benign)")
            print("=" * 80)

        try:
            result = process_with_wait(prompt, text, patterns, max_wait)
        except LLMUnavailable:
            stopped = f"Ollama was unreachable for {max_wait} min"
            break
        except KeyboardInterrupt:
            stopped = "Interrupted"
            break

        if quiet:
            done_now = sample_number - len(previous)
            elapsed = time.time() - start
            remaining = elapsed / done_now * (len(data) - sample_number)
            print(f"[{sample_number}/{len(data)}] label {actual}  prediction {result.prediction}  "
                  f"| {elapsed / 60:.1f} min elapsed, ~{remaining / 60:.0f} min left", flush=True)
        else:
            print_result(result)
        sample_lists.append(text)
        actual_values.append(actual)
        predictions.append(result.prediction)
        unsanitized_valid.append(result.unsanitized_valid)
        sanitized_valid.append(result.sanitized_valid)
        writer.writerow([sample_number, actual, result.prediction, result.unsanitized_valid, result.sanitized_valid,
                         len(result.detections), text, result.sanitized])
        predictions_file.flush()
    predictions_file.close()

    if stopped:
        print(f"\n{stopped}: stopped after {len(predictions)} of {len(data)} samples. The results below cover those "
              f"{len(predictions)}; rerun the same command with --resume to continue.")
    if not predictions:
        return predictions

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
    Statistics.confusion_matrix(filename=os.path.join(out_dir, "confusion_matrix.png"))
    Statistics.stats(filename=os.path.join(out_dir, "performance_stats.txt"))
    Statistics.print_false_negatives(sample_lists, filename=os.path.join(out_dir, "false_negatives.txt"))
    Statistics.print_false_positives(sample_lists, filename=os.path.join(out_dir, "false_positives.txt"))
    Statistics.sanitization_fail_rates(unsanitized_valid, sanitized_valid,
                                       filename=os.path.join(out_dir, "sanitization_fail_rates.png"))
    print(f"Per-sample results saved to {predictions_path}")
    return predictions


def main():
    parser = argparse.ArgumentParser(description="Run the sanitization pipeline over a labeled sample set.")
    parser.add_argument("--samples", default="resumes_half_pi",
                        help=f"sample set name ({', '.join(SAMPLE_SETS)}) or path to a CSV with text and label "
                             "columns, e.g. training/injection_detector_datasetv2.csv (default: resumes_half_pi)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help=f"trusted user prompt (default: {DEFAULT_PROMPT!r})")
    parser.add_argument("--holdout", action="store_true",
                        help="only use the rows training/train_bow.py held out from BoW training "
                             "(for the CSV the current models were trained on)")
    parser.add_argument("--limit", type=int, help="evaluate a random subset of this many samples")
    parser.add_argument("--seed", type=int, default=0, help="random seed for --limit (default: 0)")
    parser.add_argument("--out", help="output folder (default: code/results/<sample set name>)")
    parser.add_argument("--quiet", action="store_true", help="print one progress line per sample instead of its full report")
    parser.add_argument("--resume", action="store_true",
                        help="continue a stopped run: keep the samples already in the output folder's predictions.csv")
    parser.add_argument("--wait", type=float, default=10,
                        help="minutes to wait for Ollama to come back if it goes down mid-run (default: 10)")
    args = parser.parse_args()

    try:
        path = sample_path(args.samples)
        data = load_samples(args.samples)
    except ValueError as e:
        parser.error(str(e))
    total = len(data)
    if args.holdout:
        data = bow_holdout(data)
    if args.limit:
        data = random_subset(data, args.limit, args.seed)

    name = os.path.splitext(os.path.basename(path))[0]
    out_dir = args.out or os.path.join(RESULTS_DIR, name)
    injections = sum(label for _, label in data)
    print(f"Evaluating {len(data)} of {total} samples from {path} ({injections} injection, {len(data) - injections} benign)"
          f"{' [BoW holdout rows]' if args.holdout else ''}; results go to {out_dir}")
    try:
        process_predict_batch(args.prompt, data, out_dir=out_dir, quiet=args.quiet, resume=args.resume, max_wait=args.wait)
    except ResumeMismatch as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
