import re
import nltk
import spacy

nlp = spacy.load("en_core_web_sm")
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

KNOWN_INJECTION_VERBS = {
    "ignore", "disregard", "forget", "override", "overwrite", "override",
    "replace", "stop", "classify", "output", "print", "reveal",
    "list", "show", "tell", "pretend", "assume", "act", "change",
    "reset", "delete", "skip", "bypass", "suppress", "return"
}

def is_imperative_verb(token, pos_tag):
    if pos_tag == 'VB': # word is a verb. Dangerous for more creative writing such as academic papers.
    # Idea: toggle "strict" for things like datasets and turn off for resumes that should not have commands/instructions at all.
        return True
    lemma = lemmatizer.lemmatize(token.lower(), pos='v')
    # if not a verb, then check the list of known Injection verbs/
    return lemma in KNOWN_INJECTION_VERBS

class Sanitize(object):
    def __init__(self, data):
        self.data = data

    def redact(self):
        self.data = re.sub(r'<flag>.*?</flag>', '[REDACTED]', self.data, flags=re.DOTALL)
        return self.data

    def redact_injection_clause(self, matched_spans):
        # split into component sentences:
        sentences = sent_tokenize(self.data)
        result_sentences = []

        for sentence in sentences:
            # check for a matching flag in this sentence. If not found, append to the output sentence.
            matched_pattern = next((match for match in matched_spans if match.lower() in sentence.lower()), None)
            if not matched_pattern:
                result_sentences.append(sentence)
                continue

            # find where the PI starts in the sentence
            span_start = sentence.lower().find(matched_pattern.lower())
            if span_start == -1:
                result_sentences.append(sentence)
                continue

            # Redact from injection to end -- danger of missing some information -- introduce max redaction length?
            legitimate_prefix = sentence[:span_start].rstrip()
            # strip trailing conjunctions like "and", "with", "for" from the prefix
            legitimate_prefix = re.sub(r'\s+(and|or|with|for|to)\s*$', '', legitimate_prefix, flags=re.IGNORECASE)


            if legitimate_prefix:
                # add a period
                result_sentences.append(legitimate_prefix + '.')

        self.data = ' '.join(result_sentences)
        return self.data
