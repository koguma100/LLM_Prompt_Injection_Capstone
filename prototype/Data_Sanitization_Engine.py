# entry point for unsanitized data

from prototype import data, detect, sanitize
from prototype.detect import Detect
from prototype.sanitize import Sanitize

def main():
    prompts = data.Prompts().PROMPTS
    patterns = data.Patterns()
    for prompt in prompts:
        Detector = Detect(prompt, patterns)
      #  Sanitizer = Sanitize(prompt)

        # use the detection functions
        # detected_base64 = Detector.scan_base64(patterns.BASE_64_PATTERN)
        # print(detected_base64)
        # Detector.place_tags(detected_base64)
        # print(Detector.prompt)

        detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
        print("instruction overrides:", detected_instruction_overrides)
        Detector.place_tags(detected_instruction_overrides)

        detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
        print("authority overrides:", detected_authority_overrides)
        Detector.place_tags(detected_authority_overrides)

        print(Detector.prompt, "\n")


if __name__ == "__main__":
    main()


