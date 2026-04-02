import re

class Sanitize(object):
    def __init__(self, data):
        self.data = data

    def sanitize(self):
        self.data = re.sub(r'<flag>.*?</flag>', '[REDACTED]', self.data, flags=re.DOTALL)
        return self.data