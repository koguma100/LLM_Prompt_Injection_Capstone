from . import bow
from .encoding import scan_for_encoding
from .regex import place_tags, regex_scan
from .semantic import find_outlier_clauses


# Runs the detection techniques over one piece of data. place_tags updates self.prompt with the tagged text.
class Detect(object):
    def __init__(self, prompt, patterns):
        self.prompt = prompt

    def scan_for_encoding(self, text, pattern):
        return scan_for_encoding(text, pattern)

    def regex_scanner(self, pattern):
        return regex_scan(self.prompt, pattern)

    # BoW model trained to flag malicious instructions
    def BoW_malicious_scanner(self):
        return bow.bow_scan(self.prompt, bow.MALICIOUS_MODEL)

    # BoW model trained to flag any imperative sentence, benign or malicious
    def BoW_scanner(self):
        return bow.bow_scan(self.prompt, bow.IMPERATIVE_MODEL)

    def place_tags(self, substrings, start_tag="<flag>", end_tag="</flag>", extend_to_sentence_end=False):
        self.prompt = place_tags(self.prompt, substrings, start_tag, end_tag, extend_to_sentence_end)
        return self.prompt

    @staticmethod
    def find_outlier_clauses(sentence, threshold=0.4):
        return find_outlier_clauses(sentence, threshold)
