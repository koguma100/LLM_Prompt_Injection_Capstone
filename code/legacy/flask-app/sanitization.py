import sys
import os

# Add both the code directory and prototype directory to sys.path
code_dir = os.path.join(os.path.dirname(__file__), '../../')
prototype_dir = os.path.join(code_dir, 'prototype')
sys.path.insert(0, code_dir)
sys.path.insert(0, prototype_dir)

from Data_Sanitization_Engine import process_single as proto_process_single


# Wrapper to adapt prototype's process_single to Flask app's needs
def process_single(prompt, data, patterns):
    # Create a Sample object that matches prototype's expectations
    class Sample:
        def __init__(self, text):
            self.text = text
            self.prediction = 0

    sample = Sample(data)
    result = proto_process_single(prompt, sample, patterns)
    return result