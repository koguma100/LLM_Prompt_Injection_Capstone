# to run as python3 Data_sanitization_engine.py, add a dataset to data.py as an element of the Prompts class.
# performs full processing plus data results.

# Pulling from Hugging face: create a .sql file like the existing query.sql, then do duckdb < query.sql to create a csv of the query results.
# then run import utils to use the csv to python list function (I've been copying data from this output into data.py,
# so another task could be automating this into a function).

from prototype import data, detect, sanitize
from prototype.detect import Detect
from prototype.sanitize import Sanitize

class ProgramData(object):
    def __init__(self, prompts, patterns):
        self.prompts = prompts
        self.patterns = patterns

def process_batch(prompts, patterns):
    for prompt in prompts:
        process_single(prompt, patterns)

# Processing for one prompt. Take in tuple (prompt, boolean for malicious or benign), and list of regex patterns.
def process_single(prompt, patterns):
    print("ORIGINAL PROMPT:", prompt)
    Detector = initialize_detector(prompt, patterns)

    # use the detection functions
    # detected_base64 = Detector.scan_for_encoding(prompt, patterns.BASE_64_PATTERN)
    # print("Detected Base64:", detected_base64)
    # Detector.place_tags(detected_base64)
    # print(Detector.prompt)

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    print("instruction overrides:", detected_instruction_overrides)
    Detector.place_tags(detected_instruction_overrides, start_tag="<flag>", end_tag="</flag>",
                        extend_to_sentence_end=True)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    print("authority overrides:", detected_authority_overrides)
    Detector.place_tags(detected_authority_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)

    Sanitizer = initialize_sanitizer(Detector.prompt)
    Sanitizer.sanitize()
    print("SANITIZED PROMPT:", Sanitizer.prompt, "\n")

def initialize_detector(prompts, patterns):
    return Detect(prompts, patterns)

def initialize_sanitizer(prompt):
    return Sanitize(prompt)

def initialize_data(prompts, patterns):
    return ProgramData(prompts, patterns)

def main():
    Engine = initialize_data(data.Prompts.SIMPLE_PROMPTS, data.Patterns)
    for prompt in Engine.prompts:
        process_single(prompt, Engine.patterns)

if __name__ == "__main__":
    main()
