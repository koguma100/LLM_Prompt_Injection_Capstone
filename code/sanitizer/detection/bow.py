from functools import lru_cache
import os
import pickle
import re

from ..config import MODELS_DIR

# Model files in code/models/, written by code/training/train_bow.py.
# Each model has its own vectorizer, saved as <name>_vectorizer.pkl.
IMPERATIVE_MODEL = "BoWModel"
MALICIOUS_MODEL = "BoWModelMalicious"


# Loaded once per model and then reused
@lru_cache(maxsize=None)
def load_model(name):
    with open(os.path.join(MODELS_DIR, f"{name}.pkl"), 'rb') as pickledModel:
        model = pickle.load(pickledModel)
    with open(os.path.join(MODELS_DIR, f"{name}_vectorizer.pkl"), 'rb') as pickledVectorizer:
        vectorizer = pickle.load(pickledVectorizer)
    return model, vectorizer


# Sentences the model classifies as 1
def bow_scan(text, name):
    results = []
    if not text or not isinstance(text, str):
        return results
    model, vectorizer = load_model(name)

    #simple sentence splitting. Definately want to make this more robust, but requires a more comprehensive NLP
    sentences = re.split(r'(?<=[.!?])\s+', text)

    sentenceResults = model.predict(vectorizer.transform(sentences))

    for sentence, result in zip(sentences, sentenceResults):
        if result == 1:
            results.append(sentence)

    return results
