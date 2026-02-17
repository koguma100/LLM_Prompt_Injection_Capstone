from scipy.stats import entropy
from collections import Counter
import string
import numpy as np

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