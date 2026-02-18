from scipy.stats import entropy
from collections import Counter
import string
import numpy as np
import csv


# Calculate Shannon entropy. 0 -> less random (language), higher -> more random (encoding)
def calculate_entropy(s):
    # Remove Base64 padding for entropy calculation
    s = s.rstrip('=')
    if not s or len(s) < 10:  # Add minimum length check
        return 0
    counter = Counter(s)
    counts = np.array(list(counter.values()))
    probs = counts / len(s)
    return float(entropy(probs, base=2))


def csv_to_list(filepath):
    data = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header row

        for row in reader:
            if len(row) != 2:
                raise ValueError(f"Invalid row format: {row}")

            text = row[0]
            label = int(row[1])
            data.append((text, label))
        return data


# Example usage
result = csv_to_list("../hugging-face/hugging-face-samples.csv")
print(result)