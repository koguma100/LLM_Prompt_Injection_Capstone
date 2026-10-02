import re

_SENTENCE_END = re.compile(r'(?<=[.!?])\s+|$')


# Index where the sentence containing text[pos - 1] ends. Searches the full text from pos (rather than a slice)
# so the lookbehind can see a sentence-ending "." right before pos.
def sentence_end(text, pos):
    return _SENTENCE_END.search(text, pos).start()


def regex_scan(text, pattern):
    results = []
    if not text or not isinstance(text, str):
        return results
    for match in pattern.finditer(text):
        results.append(match.group())
    return results


# Wrap each occurrence of any substring in the text with start and end tags, and return the tagged text.
# optional flag: extend_to_sentence_end will place the end flag </flag> at the end of the current sentence.
def place_tags(text, substrings, start_tag="<flag>", end_tag="</flag>", extend_to_sentence_end=False):
    if not substrings:
        return text

    substrings = [s for s in substrings if s and s.strip()]
    if not substrings:
        return text

    substrings = sorted(set(substrings), key=len, reverse=True)

    if not extend_to_sentence_end:
        pattern = re.compile("|".join(re.escape(s) for s in substrings))

        def replacer(match):
            return f"{start_tag}{match.group(0)}{end_tag}"

        return pattern.sub(replacer, text)

    for substring in substrings:
        # Find all occurrences of the substring
        pattern = re.compile(re.escape(substring))

        replacements = []
        offset = 0

        for match in pattern.finditer(text):
            start_pos = match.start() + offset
            end_pos = match.end() + offset

            sentence_end_pos = sentence_end(text, end_pos)

            replacements.append((start_pos, sentence_end_pos,
                                 f"{start_tag}{text[start_pos:sentence_end_pos]}{end_tag}"))

        replacements.sort(reverse=True)
        for start, end, replacement in replacements:
            text = text[:start] + replacement + text[end:]
            offset += len(replacement) - (end - start)

    return text
