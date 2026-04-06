from app.prototype import Data_Sanitization_Engine


# Processing for one prompt. Take in Prompt object tuple and list of regex patterns.
def process_single(prompt, data, patterns):
    prediction = 0
    print("ORIGINAL DATA:\t", data)
    Detector = Data_Sanitization_Engine.Detect(data, patterns)

    # use the detection functions

    detected_instruction_overrides = Detector.regex_scanner(patterns.INSTRUCTION_OVERRIDE_PATTERN)
    if len(detected_instruction_overrides) > 0:
        prediction = 1
        print("PREDICTION UPDATED -- INSTRUCTION")
        print("instruction overrides:", detected_instruction_overrides)
    Detector.place_tags(detected_instruction_overrides, start_tag="<flag>", end_tag="</flag>",
                        extend_to_sentence_end=True)

    detected_authority_overrides = Detector.regex_scanner(patterns.AUTHORITY_PATTERN)
    if len(detected_authority_overrides) > 0:
        prediction = 1
        print("PREDICTION UPDATED -- AUTHORITY")
        print("authority overrides:", detected_authority_overrides)
    Detector.place_tags(detected_authority_overrides, start_tag="<flag>", end_tag="</flag>",extend_to_sentence_end=True)

    Sanitizer = Data_Sanitization_Engine.Sanitize(Detector.prompt)
    Sanitizer.sanitize()
    print("SANITIZED DATA:\t", Sanitizer.data,)

    output = Data_Sanitization_Engine.local_llm_call(f"{prompt}\n\Data:\n{Sanitizer.data}")
    print("LLM OUTPUT:\t\t", output)

    Data_Sanitization_Engine.test_output_validation(prompt, output)
    print("\n")
    return prediction, Sanitizer.data