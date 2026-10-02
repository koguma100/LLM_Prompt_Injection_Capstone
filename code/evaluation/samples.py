# Labeled evaluation samples. A sample set is any CSV with text and label columns (1 = prompt injection,
# 0 = benign); other columns are ignored. The named sets are the CSVs in evaluation/data/, and to add one,
# save a CSV there. Any other CSV, such as training/injection_detector_datasetv2.csv, can be loaded by path.
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SAMPLE_SETS = sorted(f[:-len(".csv")] for f in os.listdir(DATA_DIR) if f.endswith(".csv"))

# Some training texts are longer than the csv module's default 128 KB field limit
csv.field_size_limit(2**31 - 1)


# Path of a named sample set, or the given path if it's a CSV file
def sample_path(name_or_path):
    if name_or_path in SAMPLE_SETS:
        return os.path.join(DATA_DIR, f"{name_or_path}.csv")
    if os.path.isfile(name_or_path):
        return name_or_path
    raise ValueError(f"{name_or_path!r} is not a sample set ({', '.join(SAMPLE_SETS)}) or a CSV file")


# List of (text, label) tuples
def load_samples(name_or_path):
    path = sample_path(name_or_path)
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        missing = {"text", "label"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} has no {', '.join(sorted(missing))} column")
        return [(row["text"], int(row["label"])) for row in reader]
