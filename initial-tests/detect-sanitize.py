from data import Data

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')


PROMP_INJECTION_PATTERNS = [
    r'?(ignore|disrefgard) (all )?(previous|prior) instructions',
    r'disregard (the )?system prompt',
    r'pretend to be',
    r'from now on',
    r'reveal (the )?(system|hidden) prompt',
    r'\b(rm|chmod|chown|sudo|bash|sh|nc|netcat|scp|ssh)\b'
]


def preprocess(text):
    sentences = sent_tokenize(text)
    tokens = word_tokenize(text.lower())
    pos_tags = nltk.pos_tag(tokens)
    return sentences, tokens, pos_tags


if __name__ == "__main__":
    injections = Data.prompt_injections
    benigns = Data.bengin_instructions

    benign_parsed = []
    injections_parsed = []

    for line in Data.prompt_injections:
        processed = preprocess(line)
        injections_parsed.append(processed)
                                                                 
    for line in Data.bengin_instructions:
        processed = preprocess(line)
        benign_parsed.append(processed)

    print(injections_parsed)
    print(benign_parsed)
