from dataclasses import dataclass

from nltk.tokenize import sent_tokenize

from .detection import Detect
from .llm import llm_validate, local_llm_call
from .patterns import Patterns
from .sanitize import Sanitize


# Everything process_single found and produced for one piece of data
@dataclass
class Result:
    prompt: str
    original: str
    sanitized: str

    # Detections, by technique
    outlier_clauses: list
    instruction_overrides: list
    authority_overrides: list
    bow_malicious: list

    # How each detection was redacted
    standalone: list  # through the end of its sentence
    embedded: list    # as a clause inside its sentence

    # LLM answers to the prompt with each version of the data, and whether output validation judged each
    # answer relevant to the prompt. If Ollama can't be reached, process_single raises llm.LLMUnavailable.
    unsanitized_output: str
    sanitized_output: str
    unsanitized_valid: bool
    sanitized_valid: bool

    @property
    def detections(self):
        return self.instruction_overrides + self.authority_overrides + self.outlier_clauses + self.bow_malicious

    # 1 = prompt injection, 0 = benign
    # if detections found something OR if the output validator said the response doesn't make sense for the question.
    @property
    def prediction(self):
        return 1 if self.detections or not self.sanitized_valid else 0


# Detect and redact prompt injections in the data, then compare the LLM's answers to the prompt with the
# original and the sanitized data.
def process_single(prompt, data, patterns=Patterns):
    Detector = Detect(data, patterns)
    outlier_clauses = []
    # = Detector.find_outlier_clauses(data, 0.50)
    instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    bow_malicious = Detector.BoW_malicious_scanner()

    all_detections = instruction_overrides + authority_overrides + outlier_clauses + bow_malicious

    # Sanitization
    sentences = sent_tokenize(data)
    embedded_detections = [
        detection for detection in all_detections
        if any(
            detection.lower() in sent.lower() and
            not sent.strip().lower().startswith(detection.lower())
            for sent in sentences
        )
    ]

    full_sentence_detections = [d for d in all_detections if d not in embedded_detections]

    Sanitizer = Sanitize(data)

    # Redact whole sentences first, so a clause redaction can't change a flagged sentence before it's removed
    if full_sentence_detections:
        Sanitizer.redact_sentences(full_sentence_detections)

    if embedded_detections:
        Sanitizer.redact_injection_clause(embedded_detections)  # now operates on Sanitizer.data internally

    unsanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{data}")
    sanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{Sanitizer.data}")

    return Result(
        prompt=prompt,
        original=data,
        sanitized=Sanitizer.data,
        outlier_clauses=outlier_clauses,
        instruction_overrides=instruction_overrides,
        authority_overrides=authority_overrides,
        bow_malicious=bow_malicious,
        standalone=full_sentence_detections,
        embedded=embedded_detections,
        unsanitized_output=unsanitized_output,
        sanitized_output=sanitized_output,
        unsanitized_valid=llm_validate(prompt, unsanitized_output),
        sanitized_valid=llm_validate(prompt, sanitized_output),
    )
