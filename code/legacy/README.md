# Legacy

Code that is no longer used by the current pipeline, kept for reference. Nothing here is imported by the rest of `code/`, and some of it no longer runs.

| Path | Was | Why it's here |
| --- | --- | --- |
| `initial-tests/` | Sprint 1 regex + NLTK detection experiments | Superseded by `sanitizer/`; imports a `Data` class that no longer exists |
| `prototype/imports.py` | Package-style import helper | Never used; file is truncated |
| `prototype/list.py` | Empty placeholder | Empty |
| `flask-app/requirements.txt` | Flask app dependencies | Replaced by `code/requirements.txt` |
| `prototype/normalize/` | First homoglyph/leetspeak normalizer and its tests | Superseded by `sanitizer/normalize.py`, which also maps matches back to the original text |
| `flask-app/sanitization.py` | `sys.path` wrapper that let the Flask app import the prototype | `webapp/routes.py` now imports `sanitizer.pipeline` directly |
