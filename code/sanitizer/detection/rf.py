from functools import lru_cache
import os
import joblib
import re

from ..config import MODELS_DIR

# Model files in code/models/, written by code/training/train_rf.py.
# This model does not need nor have a vectorizer
IMPERATIVE_MODEL = "RFModel"
MALICIOUS_MODEL = "RFModelMalicious"


# Loaded once per model and then reused
@lru_cache(maxsize=None)
def load_model(name):

    model = joblib.load(os.path.join(MODELS_DIR, f"{name}.joblib"))

    return model


# Sentences the model classifies as 1
def rf_scan(text, name):
    results = []
    if not text or not isinstance(text, str):
        return results
    model = load_model(name)

    #simple sentence splitting. Definately want to make this more robust, but requires a more comprehensive NLP
    sentences = re.split(r'(?<=[.!?])\s+', text)

    sentenceResults = model.predict(sentences)

    for sentence, result in zip(sentences, sentenceResults):
        if result == 1:
            results.append(sentence)

    return results