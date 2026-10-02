from nltk.tokenize import sent_tokenize

from .detect import Detect
from .sanitize import Sanitize
from .prompt_hardening import test_output_validation
from .api_call import local_llm_call


class Sample(object):
    def __init__(self, text, actual_value=None):
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

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    if len(detected_instruction_overrides) > 0:
        data.prediction = 1
        print("    Instruction override matches (regex):", detected_instruction_overrides)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    if len(detected_authority_overrides) > 0:
        data.prediction = 1
        print("    Authority override matches (regex):", detected_authority_overrides)

    detected_BoW_overrides = Detector.BoW_malicious_scanner()
    if len(detected_BoW_overrides) > 0:
        data.prediction = 1
        print("    Malicious sentences (BoW model):", detected_BoW_overrides)

    all_detections = detected_instruction_overrides + detected_authority_overrides + outlier_clauses + detected_BoW_overrides
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
    return data.prediction, data.text, Sanitizer.data, unsanitized_output, sanitized_output
