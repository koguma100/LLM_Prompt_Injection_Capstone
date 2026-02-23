# to run as python3 Data_sanitization_engine.py, add a dataset to data.py as an element of the Prompts class.
# performs full processing plus data results.

# Pulling from Hugging face: create a .sql file like the existing query.sql, then do duckdb < query.sql to create a csv of the query results.
# then run import utils to use the csv to python list function (I've been copying data from this output into data.py,
# so another task could be automating this into a function).


from prototype import data, detect, sanitize
from prototype.detect import Detect
from prototype.sanitize import Sanitize
from performance_stats import PerformanceStats

class ProgramData(object):
    def __init__(self, prompts, patterns):
        self.prompts = prompts
        self.patterns = patterns

class Prompt(object):
    def __init__(self, prompt, actual_value):
        self.prompt_text = prompt
        self.actual = actual_value
        self.prediction = 0

def initialize_detector(prompts, patterns):
    return Detect(prompts, patterns)

def initialize_sanitizer(prompt):
    return Sanitize(prompt)

def initialize_data(prompts, patterns):
    return ProgramData(prompts, patterns)

# Processing for one prompt. Take in Prompt object tuple and list of regex patterns.
def process_single(prompt, patterns):
    print("ORIGINAL PROMPT:", prompt.prompt_text)
    Detector = initialize_detector(prompt.prompt_text, patterns)

    # use the detection functions

    # detected_base64 = Detector.scan_for_encoding(prompt, patterns.BASE_64_PATTERN)
   # if detected_base64 is not None: prompt.prediction = 1
    # print("Detected Base64:", detected_base64)
    # Detector.place_tags(detected_base64)
    # print(Detector.prompt)

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    if len(detected_instruction_overrides) > 0:
        prompt.prediction = 1
        print("PREDICTION UPDATED -- INSTRUCTION")
    print("instruction overrides:", detected_instruction_overrides)
    Detector.place_tags(detected_instruction_overrides, start_tag="<flag>", end_tag="</flag>",
                        extend_to_sentence_end=True)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    if len(detected_authority_overrides) > 0:
        prompt.prediction = 1
        print("PREDICTION UPDATED -- AUTHORITY")
    print("authority overrides:", detected_authority_overrides)
    Detector.place_tags(detected_authority_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)

    Sanitizer = initialize_sanitizer(Detector.prompt)
    Sanitizer.sanitize()
    print("SANITIZED PROMPT:", Sanitizer.prompt, "\n")

    return prompt.prediction

# return an array of size [prompts] for predictions
        # 0: benign
        # 1: prompt injection detected
def process_predict_batch(prompts, patterns):
    predictions = []
    actual_values = []

    for prompt_tuple in prompts:
        _prompt = Prompt(prompt_tuple[0], prompt_tuple[1])
        actual_values.append(_prompt.actual)

        prediction = process_single(_prompt, patterns)
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
    return predictions

def main():
    Engine = initialize_data(data.Prompts.HUGGING_FACE_PROMPTS, data.Patterns)
    process_predict_batch(Engine.prompts, Engine.patterns)

if __name__ == "__main__":
    main()