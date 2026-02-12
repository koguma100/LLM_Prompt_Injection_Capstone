from data import Data

import nltk
import re # regular expression
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')


PROMPT_INJECTION_PATTERNS = [
    r'(ignore|disrefgard) (all )?(previous|prior) instructions',
    r'disregard (the )?system prompt',
    r'pretend to be',
    r'from now on',
    r'reveal (the )?(system|hidden) prompt',
    r'\b(rm|chmod|chown|sudo|bash|sh|nc|netcat|scp|ssh)\b'
]

# search for regex patterns matches in the list above.
def regex_scan(text):
    flags = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(pattern)
    return flags

# separate sentences, tokens, and part of speech tags
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
    regex_prompt_injections = []
    regex_benign = []

    for line in Data.prompt_injections:
        processed = preprocess(line)
        regex_prompt_injections.append(regex_scan(line))
        injections_parsed.append(processed)
                                                                 
    for line in Data.bengin_instructions:
        processed = preprocess(line)
        regex_benign.append(regex_scan(line))
        benign_parsed.append(processed)

   # print(injections_parsed)
    #print("\n")
    #print(benign_parsed)
    print("\n")
    print("Number of pattern matches for prompt injections:", len(regex_prompt_injections))
    print("Number of pattern matches for benign instructions:", len(regex_benign))


