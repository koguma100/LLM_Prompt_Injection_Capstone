from collections import Counter
import base64
import binascii

import numpy as np
from scipy.stats import entropy


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


# scan for suspicious encoding by measuring entropy of substrings.
# should be high entropy before decoding and low entropy after decoding to have high confidence that this was encoded plaintext.
def scan_for_encoding(text, pattern):
    results = []
    # find matches of the provided regular expression
    for match in pattern.finditer(text):
        substring = match.group()

        try:
            # check if valid Base64:
            decoded = base64.b64decode(substring, validate=True)

            # calculate entropy of the substring
            entropy_substring = calculate_entropy(substring)
            entropy_decoded = calculate_entropy(decoded)

            # evaluate the entropies of the Base64 and its decoded counter to determine if this portion should be flagged:
                # entropy of plaintext: about 1-1.5
                # entropy of Base64: about 6
            #if entropy_substring > 6.0 and entropy_decoded < 1.5:
            results.append(substring)

        # substring not valid Base64
        except (binascii.Error, ValueError):
            continue

    return results
