import re

class Sanitize(object):
    def __init__(self, prompt):
        self.prompt = prompt

    def redact(self):
        self.prompt = re.sub(r'<flag>.*?</flag>', '[REDACTED]', self.prompt, flags=re.DOTALL)
        return self.prompt