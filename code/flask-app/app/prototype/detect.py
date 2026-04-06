from . import utils

import re
import base64
import binascii

class Detect(object):
    def __init__(self, prompt, patterns):
        self.prompt = prompt

# scan for suspicious encoding by measuring entropy of substrings.
    # should be high entropy before decoding and low entropy after decoding to have high confidence that this was encoded plaintext.
    def scan_for_encoding(self, text, pattern):
        results = []
        # find matches of the provided regular expression
        for match in pattern.finditer(text):
            substring = match.group()

            try:
                # check if valid Base64:
                decoded = base64.b64decode(substring, validate=True)

                # calculate entropy of the substring
                entropy_substring = utils.calcualate_entropy(substring)
                entropy_decoded = utils.calcualate_entropy(decoded)

                # evaluate the entropies of the Base64 and its decoded counter to determine if this portion should be flagged:
                    # entropy of plaintext: about 1-1.5
                    # entropy of Base64: about 6
                #if entropy_substring > 6.0 and entropy_decoded < 1.5:
                results.append(substring)

            # substring not valid Base64
            except (binascii.Error, ValueError):
                continue

        return results

    def regex_scanner(self, pattern):
            results = []
            for match in pattern.finditer(self.prompt):
                results.append(match.group())
            return results

#   Wrap each occurrence of any substring in the argument in the prompt with start and end tags.
    # optional flag: extend_to_sentence_end will plac the end flag </flag> at the end of the current sentence.
    def place_tags(self, substrings, start_tag="<flag>", end_tag="</flag>", extend_to_sentence_end=False):
        if not substrings:
            return self.prompt

        # Remove empty or whitespace-only substrings
        substrings = [s for s in substrings if s and s.strip()]
        if not substrings:
            return self.prompt

        # Sort by length (longest first) to avoid partial overlap issues
        substrings = sorted(set(substrings), key=len, reverse=True)

        if not extend_to_sentence_end:
            # Original behavior: tag only the matched substring
            pattern = re.compile("|".join(re.escape(s) for s in substrings))

            def replacer(match):
                return f"{start_tag}{match.group(0)}{end_tag}"

            self.prompt = pattern.sub(replacer, self.prompt)
        else:
            # New behavior: tag from start of substring to end of sentence
            # Create pattern to match each substring followed by content until sentence end
            # Define sentence boundaries: ., !, ?, or end of string
            sentence_end_pattern = r'(?<=[.!?])\s+|$'

            # Process each substring individually to handle overlapping cases correctly
            for substring in substrings:
                # Find all occurrences of the substring
                pattern = re.compile(re.escape(substring))

                # Keep track of replacements to avoid index shifting issues
                replacements = []
                offset = 0

                for match in pattern.finditer(self.prompt):
                    start_pos = match.start() + offset
                    end_pos = match.end() + offset

                    # Find the end of the sentence starting from the match position
                    text_after = self.prompt[end_pos:]
                    sentence_end_match = re.search(sentence_end_pattern, text_after)

                    if sentence_end_match:
                        # Extend to the end of the sentence (including punctuation)
                        sentence_end_pos = end_pos + sentence_end_match.start()
                    else:
                        # If no sentence boundary found, tag until the end of the string
                        sentence_end_pos = len(self.prompt)

                    # Store replacement info (using original positions before modifications)
                    replacements.append((start_pos, sentence_end_pos,
                                         f"{start_tag}{self.prompt[start_pos:sentence_end_pos]}{end_tag}"))

                # Apply replacements from end to start to maintain correct indices
                replacements.sort(reverse=True)
                for start, end, replacement in replacements:
                    self.prompt = self.prompt[:start] + replacement + self.prompt[end:]
                    offset += len(replacement) - (end - start)

        return None




