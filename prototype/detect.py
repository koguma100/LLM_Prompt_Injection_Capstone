import re
import base64
import binascii

class Detect(object):
    def __init__(self, prompt, patterns):
        self.prompt = prompt

    def scan_base64(self, base_64_pattern):
        results = []
        for match in base_64_pattern.finditer(self.prompt):
            candidate = match.group()
            try:
                base64.b64decode(candidate, validate=True)
                results.append(candidate)
            except binascii.Error:
                pass
        return results

    def regex_scanner(self, pattern):
        results = []
        for match in pattern.finditer(self.prompt):
            results.append(match.group())
        return results

#   Wrap each occurrence of any substring in the argument in the prompt with start and end tags.
    def place_tags(self, substrings,  start_tag="<flag>", end_tag="</flag>"):
            if not substrings:
                return self.prompt

            # Remove empty or whitespace-only substrings
            substrings = [s for s in substrings if s and s.strip()]
            if not substrings:
                return self.prompt

            # Sort by length (longest first) to avoid partial overlap issues
            substrings = sorted(set(substrings), key=len, reverse=True)

            # Create regex for each substring
            pattern = re.compile("|".join(re.escape(s) for s in substrings))

            def replacer(match):
                return f"{start_tag}{match.group(0)}{end_tag}"

            self.prompt = pattern.sub(replacer, self.prompt)
            return None




