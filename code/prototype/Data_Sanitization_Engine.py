# to run as python3 Data_sanitization_engine.py, add a dataset to data.py as an element of the Prompts class.
# performs full processing plus data results.
# Pulling from Hugging face: create a .sql file like the existing query.sql, then do duckdb < query.sql to create a csv of the query results.
# then run import utils to use the csv to python list function (I've been copying data from this output into data.py,
# so another task could be automating this into a function).

from detect import Detect
from sanitize import Sanitize
from nltk.tokenize import sent_tokenize
from data import Prompts
from data import Patterns
from performance_stats import PerformanceStats
from prompt_hardening import test_output_validation
from api_call import local_llm_call


class ProgramData(object):
    def __init__(self, prompt, data, patterns):
        self.data = data
        self.prompt = prompt
        self.patterns = patterns

class Sample(object):
    def __init__(self, text, actual_value):
        self.text = text
        self.actual = actual_value
        self.prediction = 0
        self.unsanitized_valid = True
        self.sanitized_valid = True

def initialize_detector(prompts, patterns):
    return Detect(prompts, patterns)

def initialize_sanitizer(prompt):
    return Sanitize(prompt)

# Processing for one prompt. Take in Prompt object tuple and list of regex patterns.
def process_single(prompt, data, patterns):
    print("[1] ORIGINAL INPUT DATA:\n   ", data.text)
    print("\n[2] DETECTION RESULTS:")

    Detector = initialize_detector(data.text, patterns)
    outlier_clauses = Detector.find_outlier_clauses(data.text, 0.50)
    if len(outlier_clauses) > 0:
        data.prediction = 1
        print("    Outlier clauses (semantic outliers):", outlier_clauses)

    # use the detection functions

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    if len(detected_instruction_overrides) > 0:
        data.prediction = 1
        print("PREDICTION UPDATED -- INSTRUCTION")
        print("instruction overrides:", detected_instruction_overrides)
    Detector.place_tags(detected_instruction_overrides, start_tag="<flag>", end_tag="</flag>",
                        extend_to_sentence_end=True)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    if len(detected_authority_overrides) > 0:
        data.prediction = 1
        print("    Authority override matches (regex):", detected_authority_overrides)

    all_detections = detected_instruction_overrides + detected_authority_overrides + outlier_clauses
    if not all_detections:
        print("    No prompt injections detected")

    # Sanitization
    sentences = sent_tokenize(data.text)
    embedded_detections = [
        detection for detection in all_detections
        if any(
            detection.lower() in sent.lower() and
            not sent.strip().lower().startswith(detection.lower())
            for sent in sentences
        )
    ]

    full_sentence_detections = [d for d in all_detections if d not in embedded_detections]
        print("PREDICTION UPDATED -- AUTHORITY")
        print("authority overrides:", detected_authority_overrides)
    Detector.place_tags(detected_authority_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)

    '''
    detected_BoW_malicious_overrides = Detector.BoW_malicious_scanner()
    if len(detected_BoW_malicious_overrides) > 0:
            prompt.prediction = 1
            print("PREDICTION UPDATED -- BoW(MALICIOUS)")
    print("Predicted Malicious Sentences:", detected_BoW_malicious_overrides)
    Detector.place_tags(detected_BoW_malicious_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)
    '''

    detected_BoW_overrides = Detector.BoW_malicious_scanner()
    if len(detected_BoW_overrides) > 0:
            prompt.prediction = 1
            print("PREDICTION UPDATED -- BoW(MALICIOUS)")
    print("Predicted Malicious Sentences:", detected_BoW_overrides)
    Detector.place_tags(detected_BoW_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)


    Sanitizer = initialize_sanitizer(data.text)

    if embedded_detections:
        print("    Embedded injections (redacting clause only):", embedded_detections)
        Sanitizer.redact_injection_clause(embedded_detections)  # now operates on Sanitizer.data internally

    if full_sentence_detections:
        print("    Standalone injections (redacting full sentence):", full_sentence_detections)
        StandaloneDetector = initialize_detector(Sanitizer.data, patterns)
        StandaloneDetector.place_tags(full_sentence_detections, start_tag="<flag>", end_tag="</flag>",
                                      extend_to_sentence_end=True)
        Sanitizer = initialize_sanitizer(StandaloneDetector.prompt)
        Sanitizer.redact()

    print("\n[3] SANITIZATION:")
    print("    Before sanitization:", Detector.prompt)
    print("    After sanitization: ", Sanitizer.data)

    # Get LLM response with unsanitized data
    unsanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{data.text}")
    print("\n[4] LLM RESPONSES:")
    print("    Response to UNSANITIZED data:", unsanitized_output)
    Sanitizer = initialize_sanitizer(Detector.prompt)
    Sanitizer.redact()
    print("SANITIZED DATA:\t", Sanitizer.data,)

    output = local_llm_call(f"{prompt}\n\nResume:\n{Sanitizer.data}")
    print("LLM OUTPUT:\t\t", output)

    test_output_validation(prompt, output)
    # Get LLM response with sanitized data
    sanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{Sanitizer.data}")
    print("    Response to SANITIZED data:  ", sanitized_output)

    print("\n[5] OUTPUT VALIDATION:")
    print("    Response to UNSANITIZED data -> ", end="")
    data.unsanitized_valid = test_output_validation(prompt, unsanitized_output)
    print("    Response to SANITIZED data   -> ", end="")
    valid_response = test_output_validation(prompt, sanitized_output)
    data.sanitized_valid = valid_response
    if valid_response is False:
        data.prediction = 1
    print("\n[6] FINAL PREDICTION:", "1 (prompt injection)" if data.prediction == 1 else "0 (benign)")
    print("\n")
    return data.prediction, Sanitizer.data


# return an array of size [prompts] for predictions
        # 0: benign
        # 1: prompt injection detected
def process_predict_batch(prompt, data, patterns):
    predictions = []
    actual_values = []

    for data_tuple in data:
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
    Statistics.confusion_matrix()
    Statistics.stats()
    Statistics.print_false_negatives(sample_lists)
    Statistics.print_false_positives(sample_lists)
    Statistics.sanitization_fail_rates(unsanitized_valid, sanitized_valid)
    return predictions

def main():

    Engine = ProgramData("Should I hire this person as an entry level cybersecurity analyst?", Prompts.RESUMES_HALF_PI, Patterns)
    Engine = ProgramData("Should I hire this person as an entry level cybersecurity analyst?", Prompts.RESUMES, Patterns)
    process_predict_batch(Engine.prompt, Engine.data, Engine.patterns)

if __name__ == "__main__":
    main()
