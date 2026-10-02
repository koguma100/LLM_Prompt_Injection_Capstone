# Batch evaluation of the sanitization pipeline. From the code/ directory run:
#     python -m evaluation.run_eval
# To evaluate a different dataset, add it to evaluation/samples.py as an element of the Prompts class
# and pass it to ProgramData in main(). Outputs (stats, plots, false positives/negatives) go to code/results/.
# Pulling from Hugging face: create a .sql file like the existing hugging-face/query.sql, then do duckdb < query.sql
# to create a csv of the query results. Then use evaluation.utils.csv_to_list to turn the csv into a python list
# (I've been copying data from this output into samples.py, so another task could be automating this into a function).

import os

from sanitizer.metrics import PerformanceStats
from sanitizer.patterns import Patterns
from sanitizer.pipeline import Sample, process_single
from evaluation.samples import Prompts

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


class ProgramData(object):
    def __init__(self, prompt, data, patterns):
        self.data = data
        self.prompt = prompt
        self.patterns = patterns


# return an array of size [prompts] for predictions
        # 0: benign
        # 1: prompt injection detected
def process_predict_batch(prompt, data, patterns):
    predictions = []
    actual_values = []
    sample_lists = []
    unsanitized_valid = []
    sanitized_valid = []
    print("\n\n")
    for sample_number, data_tuple in enumerate(data, 1):
        sample = Sample(data_tuple[0], data_tuple[1])
        print("=" * 80)
        print(f"SAMPLE {sample_number}/{len(data)}  |  Actual label:", "1 (prompt injection)" if sample.actual == 1 else "0 (benign)")
        print("=" * 80)
        sample_lists.append(sample.text)
        actual_values.append(sample.actual)

        prediction, _, sanitized, _, _ = process_single(prompt, sample, patterns)
        predictions.append(prediction)
        unsanitized_valid.append(sample.unsanitized_valid)
        sanitized_valid.append(sample.sanitized_valid)

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
    os.makedirs(RESULTS_DIR, exist_ok=True)
    Engine = ProgramData("Should I hire this person as an entry level cybersecurity analyst?", Prompts.RESUMES_HALF_PI, Patterns)
    process_predict_batch(Engine.prompt, Engine.data, Engine.patterns)

if __name__ == "__main__":
    main()
