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


# search for regex patterns matches in the list above.
def regex_scan(text):
    flags = []
    for pattern in Data.PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re):
            flags.append(text)
    return flags

def imperative_scan(text):
    pass

# separate sentences, tokens, and part of speech tags
def preprocess(text):
    sentences = sent_tokenize(text)
    tokens = word_tokenize(text.lower())
    pos_tags = nltk.pos_tag(tokens)
    return sentences, tokens, pos_tags

class Parse:
    sentences = []
    tokens = []
    pos_tags = []
    regex_flags = []

if __name__ == "__main__":
    injections = Data.prompt_injections
    benigns = Data.bengin_instructions
    Injections_Parse = Parse()
    Benign_Parse = Parse()

    for line in injections:
        sentences, tokens, pos_tags = preprocess(line)
        Injections_Parse.sentences.extend(sentences)

    for line in benigns:
        sentences, tokens, pos_tags = preprocess(line)
        Benign_Parse.sentences.extend(sentences)

    for sentence in Injections_Parse.sentences:
        print(sentence)
        Injections_Parse.regex_flags.append(regex_scan(sentence))

    for sentence in Benign_Parse.sentences:
        print(sentence)
        Benign_Parse.regex_flags.append(regex_scan(sentence))


    print("Number of pattern matches for prompt injections:", len(Injections_Parse.regex_flags))
    print("Number of pattern matches for benign instructions:", len(Benign_Parse.regex_flags))

    print(Injections_Parse.regex_flags)
