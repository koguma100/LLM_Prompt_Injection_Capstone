import re
from nltk.tokenize import sent_tokenize

# Conjunctions/prepositions that can dangle at either end of a cut
_TRAILING_JOINERS = re.compile(
    r'\s+(and|or|with|for|to|but|yet|so|while|as|by)\s*$',
    re.IGNORECASE
)
_LEADING_JOINERS = re.compile(
    r'^(and|or|with|for|to|but|yet|so|while|as|by)\s+',
    re.IGNORECASE
)


def strip_dangling_conjunctions(text: str) -> str:
    text = _TRAILING_JOINERS.sub('', text).rstrip()
    text = _LEADING_JOINERS.sub('', text).lstrip()
    return text


def _find_earliest_injection(sentence: str, matched_spans: list[str]) -> tuple[int, str] | None:
    earliest_idx = len(sentence)
    earliest_span = None

    for span in matched_spans:
        idx = sentence.lower().find(span.lower())
        if idx != -1 and idx < earliest_idx:
            earliest_idx = idx
            earliest_span = span

    return (earliest_idx, earliest_span) if earliest_span is not None else None


class Sanitize(object):
    def __init__(self, data: str):
        self.data = data

    def redact(self) -> str:
        self.data = re.sub(r'<flag>.*?</flag>', '[REDACTED]', self.data, flags=re.DOTALL)
        return self.data

    def redact_injection_clause(self, matched_spans: list[str]) -> str:
        sentences = sent_tokenize(self.data)
        result_sentences = []

        for sentence in sentences:
            current = sentence
            # Keep removing spans until none remain in this sentence
            while True:
                hit = _find_earliest_injection(current, matched_spans)
                if hit is None:
                    break

                span_start, matched_span = hit
                span_end = span_start + len(matched_span)

                prefix = current[:span_start].rstrip()
                suffix = current[span_end:].lstrip()

                if not prefix:
                    suffix = _LEADING_JOINERS.sub('', suffix).lstrip()

                if prefix and suffix:
                    current = prefix + ' ' + suffix
                elif prefix:
                    current = prefix + '.'
                elif suffix:
                    current = suffix
                else:
                    current = ''
                    break

            # Clean up double commas and comma-space-comma artifacts
            current = re.sub(r',\s*,', ',', current)
            current = re.sub(r',\s*(and|or)\s*,', r', \1', current, flags=re.IGNORECASE)

            if current.strip():
                result_sentences.append(current)

        self.data = ' '.join(result_sentences)
        return self.data
