from functools import lru_cache
import re

import numpy as np

from ..config import SENTENCE_MODEL


# Loaded on first use and then reused, since loading the model takes a few seconds
@lru_cache(maxsize=None)
def _sentence_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(SENTENCE_MODEL)


def split_into_clauses(sentence):
    # Split on punctuation/conjunctions — adjust as needed
    if not sentence or not isinstance(sentence, str):
        return []
    return [c.strip() for c in re.split(r'[,;]|\band\b|\bbut\b|\bor\b', sentence) if c.strip()]


# Clauses whose embedding is far (cosine distance > threshold) from the mean embedding of all clauses
def find_outlier_clauses(sentence, threshold=0.4):
    clauses = split_into_clauses(sentence)
    if len(clauses) < 2:
        return []

    embeddings = _sentence_model().encode(clauses)
    centroid = embeddings.mean(axis=0)
    distances = [
        1 - np.dot(e, centroid) / (np.linalg.norm(e) * np.linalg.norm(centroid))
        for e in embeddings
    ]
    return [clause for clause, dist in zip(clauses, distances) if dist > threshold]
