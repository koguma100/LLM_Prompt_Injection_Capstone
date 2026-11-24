from dataclasses import dataclass, field
from typing import Optional

from nltk.tokenize import sent_tokenize

from .config import DETECTOR_WEIGHTS, INJECTION_THRESHOLD, SKIP_LLM_THRESHOLD
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
    bow_malicious: list  # retired BoW detector; always empty now, kept so saved results still load

    # How each detection was redacted
    standalone: list  # through the end of its sentence
    embedded: list    # as a clause inside its sentence

    # LLM answers to the prompt with each version of the data, and whether output validation judged each
    # answer relevant to the prompt. If Ollama can't be reached, process_single raises llm.LLMUnavailable.
    # All four are None when the cheap detectors' vote skipped the LLM stage (see llm_skipped).
    unsanitized_output: Optional[str]
    sanitized_output: Optional[str]
    unsanitized_valid: Optional[bool]
    sanitized_valid: Optional[bool]

    # Weighted vote of the cheap detectors (see config.DETECTOR_WEIGHTS), and whether it was high enough
    # to skip the LLM stage
    cheap_score: float = 0.0
    llm_skipped: bool = False

    # Sentences the Random Forest classifier flagged
    rf_malicious: list = field(default_factory=list)

    @property
    def detections(self):
        return (self.instruction_overrides + self.authority_overrides + self.outlier_clauses + self.bow_malicious
                + self.rf_malicious)

    # Weighted vote of every detector, including output validation of the answer from the sanitized data
    # (see config.DETECTOR_WEIGHTS)
    @property
    def score(self):
        return cheap_vote({
            "rf_malicious": self.rf_malicious,
            "instruction_overrides": self.instruction_overrides,
            "authority_overrides": self.authority_overrides,
            "outlier_clauses": self.outlier_clauses,
            "bow_malicious": self.bow_malicious,
            "llm_validation": self.sanitized_valid is False,
        })

    # 1 = prompt injection, 0 = benign
    @property
    def prediction(self):
        return 1 if self.score >= INJECTION_THRESHOLD else 0


# Weighted vote: each detector that found anything adds its weight once, however many matches it had.
# detections maps detector name -> its matches (or a bool).
def cheap_vote(detections, weights=DETECTOR_WEIGHTS):
    return sum(weights.get(name, 0) for name, matches in detections.items() if matches)


# Detect and redact prompt injections in the data, then compare the LLM's answers to the prompt with the
# original and the sanitized data. If the cheap detectors' vote reaches skip_threshold, the LLM stage is skipped
# (skip_threshold=None always runs it).
def process_single(prompt, data, patterns=Patterns, skip_threshold=SKIP_LLM_THRESHOLD):
    Detector = Detect(data, patterns)
    outlier_clauses = []
    # = Detector.find_outlier_clauses(data, 0.50)
    instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    rf_malicious = Detector.RF_malicious_scanner()

    all_detections = instruction_overrides + authority_overrides + outlier_clauses + rf_malicious
    score = cheap_vote({
        "instruction_overrides": instruction_overrides,
        "authority_overrides": authority_overrides,
        "outlier_clauses": outlier_clauses,
        "rf_malicious": rf_malicious,
    })
    llm_skipped = skip_threshold is not None and score >= skip_threshold

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

    # The expensive stage: two LLM answers and two output validations
    if llm_skipped:
        unsanitized_output = sanitized_output = unsanitized_valid = sanitized_valid = None
    else:
        unsanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{data}")
        sanitized_output = local_llm_call(f"{prompt}\n\nResume:\n{Sanitizer.data}")
        unsanitized_valid = llm_validate(prompt, unsanitized_output)
        sanitized_valid = llm_validate(prompt, sanitized_output)

    return Result(
        prompt=prompt,
        original=data,
        sanitized=Sanitizer.data,
        outlier_clauses=outlier_clauses,
        instruction_overrides=instruction_overrides,
        authority_overrides=authority_overrides,
        bow_malicious=[],
        standalone=full_sentence_detections,
        embedded=embedded_detections,
        unsanitized_output=unsanitized_output,
        sanitized_output=sanitized_output,
        unsanitized_valid=unsanitized_valid,
        sanitized_valid=sanitized_valid,
        cheap_score=score,
        llm_skipped=llm_skipped,
        rf_malicious=rf_malicious,
    )
