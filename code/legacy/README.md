# Legacy

Code that is no longer used by the current pipeline, kept for reference. Nothing here is imported by the rest of `code/`, and some of it no longer runs.

| Path | Was | Why it's here |
| --- | --- | --- |
| `initial-tests/` | Sprint 1 regex + NLTK detection experiments | Superseded by `sanitizer/`; imports a `Data` class that no longer exists |
| `prototype/imports.py` | Package-style import helper | Never used; file is truncated |
| `prototype/list.py` | Empty placeholder | Empty |
| `prototype/normalize/` | First homoglyph/leetspeak normalizer and its tests | Superseded by `sanitizer/normalize.py`, which also maps matches back to the original text |
