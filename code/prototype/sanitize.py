import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

class Sanitize(object):
    def __init__(self, data):
        self.data = data

    def redact(self):
        self.data = re.sub(r'<flag>.*?</flag>', '[REDACTED]', self.data, flags=re.DOTALL)
        return self.data

    def soften_imperatives(self):
        def process_flagged(match):
            flagged_text = match.group(1)
            sentences = sent_tokenize(flagged_text)
            result = []

            for sent in sentences:
                tokens = word_tokenize(sent)
                tags = nltk.pos_tag(tokens)

                if tags and tags[0][1] == 'VB':
                    verb = tags[0][0]
                    rest = ' '.join(tokens[1:])
                    softened = f"[Attempted instruction: '{verb}' command detected] {rest}"
                    result.append(softened)
                else:
                    result.append(sent)

            return ' '.join(result)

        self.data = re.sub(r'<flag>(.*?)</flag>', process_flagged, self.data, flags=re.DOTALL)
        return self.data