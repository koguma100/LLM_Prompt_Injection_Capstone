import re


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

    sentence_end_pattern = r'(?<=[.!?])\s+|$'

    for substring in substrings:
        # Find all occurrences of the substring
        pattern = re.compile(re.escape(substring))

        replacements = []
        offset = 0

        for match in pattern.finditer(text):
            start_pos = match.start() + offset
            end_pos = match.end() + offset

            text_after = text[end_pos:]
            sentence_end_match = re.search(sentence_end_pattern, text_after)

            if sentence_end_match:
                sentence_end_pos = end_pos + sentence_end_match.start()
            else:
                sentence_end_pos = len(text)

            replacements.append((start_pos, sentence_end_pos,
                                 f"{start_tag}{text[start_pos:sentence_end_pos]}{end_tag}"))

        replacements.sort(reverse=True)
        for start, end, replacement in replacements:
            text = text[:start] + replacement + text[end:]
            offset += len(replacement) - (end - start)

    return text
