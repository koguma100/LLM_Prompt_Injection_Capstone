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

def initialize_detector(prompts, patterns):
    return Detect(prompts, patterns)

def initialize_sanitizer(prompt):
    return Sanitize(prompt)

# Processing for one prompt. Take in Prompt object tuple and list of regex patterns.
def process_single(prompt, data, patterns):
    print("ORIGINAL DATA:\t", data.text)
    Detector = initialize_detector(data.text, patterns)

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    if len(detected_instruction_overrides) > 0:
        data.prediction = 1
        print("Instruction overrides:", detected_instruction_overrides)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    if len(detected_authority_overrides) > 0:
        data.prediction = 1
        print("Authority overrides:", detected_authority_overrides)

    all_detections = detected_instruction_overrides + detected_authority_overrides

    # Find PI's that are embedded midsentence, and modify with more granularity.
    sentences = sent_tokenize(data.text)
    embedded_detections = [
        detection for detection in all_detections
        if any(
            detection.lower() in sent.lower() and
            not sent.strip().lower().startswith(detection.lower())
            for sent in sentences
        )
    ]

    # Find PI that are entire sentences and redact fully (ones that were not determined to be embedded above)
    full_sentence_detections = [detection for detection in all_detections if detection not in embedded_detections]

    Sanitizer = initialize_sanitizer(data.text)
    if embedded_detections:
        print("Embedded injections:", embedded_detections)
        Sanitizer.redact_injection_clause(embedded_detections)

    # Fully redact full sentence prompt injections
    if full_sentence_detections:
        print("Standalone injections:", full_sentence_detections)
        StandaloneDetector = initialize_detector(Sanitizer.data, patterns)
        StandaloneDetector.place_tags(full_sentence_detections, start_tag="<flag>", end_tag="</flag>",
                                      extend_to_sentence_end=True)
        Sanitizer = initialize_sanitizer(StandaloneDetector.prompt)
        Sanitizer.redact()

    print("BEFORE SANITIZED:\t", Detector.prompt)
    print("SANITIZED DATA:\t", Sanitizer.data)

    output = local_llm_call(f"{prompt}\n\nResume:\n{Sanitizer.data}")
    print("LLM OUTPUT:\t\t", output)
    test_output_validation(prompt, output)
    print("\n")
    return data.prediction, Sanitizer.data


# return an array of size [prompts] for predictions
        # 0: benign
        # 1: prompt injection detected
def process_predict_batch(prompt, data, patterns):
    predictions = []
    actual_values = []
    sample_lists = []
    print("\n\n")
    for data_tuple in data:
        sample = Sample(data_tuple[0], data_tuple[1])
        sample_lists.append(sample.text)
        actual_values.append(sample.actual)

        prediction, sanitized = process_single(prompt, sample, patterns)
        predictions.append(prediction)

    print("System predictions\t", end='')
    for i in predictions:
        print(i, end='')

    print("\nActual value\t\t", end='')
    for j in actual_values:
        print(j, end='')
    print("\n")
    Statistics = PerformanceStats(actual_values, predictions)
    Statistics.confusion_matrix()
    Statistics.stats()
    Statistics.print_false_negatives(sample_lists)
    Statistics.print_false_positives(sample_lists)
    return predictions

def main():

    Engine = ProgramData("Should I hire this person as an entry level cybersecurity analyst?", Prompts.embedded_PI_tests, Patterns)
    process_predict_batch(Engine.prompt, Engine.data, Engine.patterns)

if __name__ == "__main__":
    main()
