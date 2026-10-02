# Labeled evaluation samples: one CSV per sample set in evaluation/data/, with columns text,label
# (1 = prompt injection, 0 = benign). To add a sample set, save a CSV with those columns in that folder.
import os

from .utils import csv_to_list

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SAMPLE_SETS = sorted(f[:-len(".csv")] for f in os.listdir(DATA_DIR) if f.endswith(".csv"))


# List of (text, label) tuples
def load_samples(name):
    return csv_to_list(os.path.join(DATA_DIR, f"{name}.csv"))
