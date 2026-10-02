import re


class Patterns:
    # regular expression for instruction override
    INSTRUCTION_OVERRIDE_PATTERN = re.compile(
    r'(ignore|disregard|forget).{0,20}(previous|prior|above|all)?.{0,20}(limitations|instructions|commands|tasks|directions|everything)',
    re.IGNORECASE | re.DOTALL
)

    AUTHORITY_PATTERN = re.compile(
        r'i am (the |your )?(system administrator|sudo|root|admin|superuser)'
        r'|you are (talking to|speaking with) (the |your )?(system admin|sudo|root|admin|superuser)'
        r'|(system admin|sudo|root|admin|superuser) (speaking|here|talking)'
        r'|(Show me|i order you|print|tell me)',
        re.IGNORECASE
    )

    # regular expression for Base 64
    BASE_64_PATTERN = re.compile(
         r'[A-Za-z0-9+/]{20,}={0,2}'
    )
