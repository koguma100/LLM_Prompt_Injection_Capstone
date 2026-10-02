from . import utils
from sentence_transformers import SentenceTransformer
import re
import base64
import numpy as np
import binascii
import pickle
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

# pickled BoW models live in code/models/ (train them with code/training/), so detection works from any working directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')


def split_into_clauses(sentence):
    # Split on punctuation/conjunctions — adjust as needed
    if not sentence or not isinstance(sentence, str):
        return []
    return [c.strip() for c in re.split(r'[,;]|\band\b|\bbut\b|\bor\b', sentence) if c.strip()]


class Detect(object):
    def __init__(self, prompt, patterns):
        self.prompt = prompt

# scan for suspicious encoding by measuring entropy of substrings.
    # should be high entropy before decoding and low entropy after decoding to have high confidence that this was encoded plaintext.
    def scan_for_encoding(self, text, pattern):
        results = []
        # find matches of the provided regular expression
        for match in pattern.finditer(text):
            substring = match.group()

            try:
                # check if valid Base64:
                decoded = base64.b64decode(substring, validate=True)

                # calculate entropy of the substring
                entropy_substring = utils.calculate_entropy(substring)
                entropy_decoded = utils.calculate_entropy(decoded)

                # evaluate the entropies of the Base64 and its decoded counter to determine if this portion should be flagged:
                    # entropy of plaintext: about 1-1.5
                    # entropy of Base64: about 6
                #if entropy_substring > 6.0 and entropy_decoded < 1.5:
                results.append(substring)

            # substring not valid Base64
            except (binascii.Error, ValueError):
                continue

        return results

    def regex_scanner(self, pattern):
            results = []
            if not self.prompt or not isinstance(self.prompt, str):
                return results
            for match in pattern.finditer(self.prompt):
                results.append(match.group())
            return results
    #kind of messy, perhaps restructure our detection pipeline so models are opened at the beginning?
    def BoW_malicious_scanner(self):
        return self._BoW_scan('BoWModelMalicious.pkl')

    def BoW_scanner(self):
        return self._BoW_scan('BoWModel.pkl')

    def _BoW_scan(self, model_filename):
        with open(os.path.join(MODEL_DIR, model_filename), 'rb') as pickledModel:
            model = pickle.load(pickledModel)
        with open(os.path.join(MODEL_DIR, 'vectorizer.pkl'), 'rb') as pickledVectorizer:
            vectorizer = pickle.load(pickledVectorizer)

        results = []
        if not self.prompt or not isinstance(self.prompt, str):
            return results
        #simple sentence splitting. Definately want to make this more robust, but requires a more comprehensive NLP
        sentences = re.split(r'(?<=[.!?])\s+', self.prompt)

        sentenceResults = model.predict(vectorizer.transform(sentences))

        for sentence, result in zip(sentences, sentenceResults):
            if result == 1:
                results.append(sentence)

        return results

#   Wrap each occurrence of any substring in the argument in the prompt with start and end tags.
    # optional flag: extend_to_sentence_end will plac the end flag </flag> at the end of the current sentence.
    def place_tags(self, substrings, start_tag="<flag>", end_tag="</flag>", extend_to_sentence_end=False):
        if not substrings:
            return self.prompt

        substrings = [s for s in substrings if s and s.strip()]
        if not substrings:
            return self.prompt

        substrings = sorted(set(substrings), key=len, reverse=True)

        if not extend_to_sentence_end:
            pattern = re.compile("|".join(re.escape(s) for s in substrings))

            def replacer(match):
                return f"{start_tag}{match.group(0)}{end_tag}"

            self.prompt = pattern.sub(replacer, self.prompt)
        else:
            sentence_end_pattern = r'(?<=[.!?])\s+|$'

            for substring in substrings:
                # Find all occurrences of the substring
                pattern = re.compile(re.escape(substring))

                replacements = []
                offset = 0

                for match in pattern.finditer(self.prompt):
                    start_pos = match.start() + offset
                    end_pos = match.end() + offset

                    text_after = self.prompt[end_pos:]
                    sentence_end_match = re.search(sentence_end_pattern, text_after)

                    if sentence_end_match:
                        sentence_end_pos = end_pos + sentence_end_match.start()
                    else:
                        sentence_end_pos = len(self.prompt)

                    replacements.append((start_pos, sentence_end_pos,
                                         f"{start_tag}{self.prompt[start_pos:sentence_end_pos]}{end_tag}"))

                replacements.sort(reverse=True)
                for start, end, replacement in replacements:
                    self.prompt = self.prompt[:start] + replacement + self.prompt[end:]
                    offset += len(replacement) - (end - start)

        return None

    @staticmethod
    def find_outlier_clauses(sentence, threshold=0.4):
        clauses = split_into_clauses(sentence)
        if len(clauses) < 2:
            return []

        embeddings = model.encode(clauses)
        centroid = embeddings.mean(axis=0)
        distances = [
            1 - np.dot(e, centroid) / (np.linalg.norm(e) * np.linalg.norm(centroid))
            for e in embeddings
        ]
        return [clause for clause, dist in zip(clauses, distances) if dist > threshold]

