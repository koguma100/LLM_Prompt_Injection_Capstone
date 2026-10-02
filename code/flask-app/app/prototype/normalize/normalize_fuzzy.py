"""
Normalize untrusted data into a detection-only copy that collapses common
obfuscation tricks, while remembering where every character came from.

The normalized text is never sent to the LLM or shown to the user. It is only
scanned for injection patterns; any match is mapped back to the original text
with NormalizedText.original_span(), and redaction happens on the original.
Because of that, normalization can be aggressive without destroying data.

Internally the text is a list of (char, start, end) triples, where [start, end)
is the span of the ORIGINAL text that produced the char. Every stage consumes
and returns that list, so offsets survive deletions, merges and decodings.
"""

import base64
import binascii
import html
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import unquote

from confusables import confusable_characters


@dataclass
class NormalizedText:
    text: str
    starts: list
    ends: list
    original: str

    def original_span(self, start, end):
        """Map a [start, end) span of self.text to a span of self.original."""
        if start >= end:
            pos = self.starts[start] if start < len(self.starts) else len(self.original)
            return pos, pos
        return min(self.starts[start:end]), max(self.ends[start:end])


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _apply(chars, pattern, replace):
    """Run `pattern` over the current text and splice in replace(match, chunk).

    `chunk` is the slice of triples the match covers. `replace` returns a new
    list of triples, or None to leave the match unchanged.
    """
    text = ''.join(c for c, _, _ in chars)
    out, last = [], 0
    for m in pattern.finditer(text):
        new = replace(m, chars[m.start():m.end()])
        if new is None:
            continue
        out.extend(chars[last:m.start()])
        out.extend(new)
        last = m.end()
    out.extend(chars[last:])
    return out


def _spread(text, start, end):
    """Give every char of `text` the same original span."""
    return [(c, start, end) for c in text]


def _chunk_span(chunk):
    return chunk[0][1], chunk[-1][2]


# ---------------------------------------------------------------------------
# 1. decoding: reveal text that was hidden or encoded
# ---------------------------------------------------------------------------

def _decode_tag_chars(chars):
    """Unicode tag characters (U+E0020-E007E) mirror ASCII but render invisibly.

    They are used to smuggle whole instructions past a human reader, so decode
    them to the ASCII they stand for instead of dropping them.
    """
    out = []
    for c, s, e in chars:
        cp = ord(c)
        if 0xE0020 <= cp <= 0xE007E:
            out.append((chr(cp - 0xE0000), s, e))
        elif cp in (0xE0001, 0xE007F):  # tag begin / cancel markers
            continue
        else:
            out.append((c, s, e))
    return out


HTML_ENTITY_RE = re.compile(r'&(?:#\d{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});')
URL_ESCAPE_RE = re.compile(r'(?:%[0-9A-Fa-f]{2})+')
BASE64_RE = re.compile(r'(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])')


def _decode_html_entities(chars):
    def replace(m, chunk):
        decoded = html.unescape(m.group())
        return None if decoded == m.group() else _spread(decoded, *_chunk_span(chunk))
    # twice, for double-encoded data like "&amp;#x200B;"
    return _apply(_apply(chars, HTML_ENTITY_RE, replace), HTML_ENTITY_RE, replace)


def _decode_url_escapes(chars):
    def replace(m, chunk):
        return _spread(unquote(m.group(), errors='replace'), *_chunk_span(chunk))
    return _apply(chars, URL_ESCAPE_RE, replace)


def _looks_like_text(s):
    if not s.strip() or not all(c.isprintable() or c.isspace() for c in s):
        return False
    readable = sum(c.isalpha() or c.isspace() for c in s)
    return readable / len(s) >= 0.8


def _decode_base64(chars):
    """Replace base64 runs that decode to readable text with the decoded text.

    Long words, hashes and IDs are also valid base64 alphabet, but they almost
    never decode to printable UTF-8 prose, so they are left alone.
    """
    def replace(m, chunk):
        token = m.group()
        if len(token) % 4:
            return None
        try:
            decoded = base64.b64decode(token, validate=True).decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            return None
        if not _looks_like_text(decoded):
            return None
        return _spread(decoded, *_chunk_span(chunk))
    return _apply(chars, BASE64_RE, replace)


# ---------------------------------------------------------------------------
# 2. unicode: drop invisibles, fold width/case/accents, map homoglyphs
# ---------------------------------------------------------------------------

def _drop_invisible(chars):
    """Remove format characters: zero-width chars, soft hyphens, BOMs, bidi overrides."""
    return [t for t in chars if unicodedata.category(t[0]) != 'Cf']


def _fold(chars):
    """NFKC (fullwidth, math letters, ligatures), casefold, then strip accents."""
    out = []
    for c, s, e in chars:
        folded = unicodedata.normalize('NFD', unicodedata.normalize('NFKC', c).casefold())
        out.extend((f, s, e) for f in folded if unicodedata.category(f) != 'Mn')
    return out


def _script(c):
    return unicodedata.name(c, '').split(' ')[0]


@lru_cache(maxsize=None)
def _ascii_lookalike(c):
    """Return the lowercase ASCII letter `c` is confusable with, else None."""
    letters = {x.lower() for x in (confusable_characters(c) or []) if x.isascii() and x.isalpha()}
    return min(letters) if letters else None


WORD_RE = re.compile(r'\w+')


def _map_homoglyphs(chars):
    """Swap lookalike letters for ASCII, only in words that look spoofed.

    A word is treated as spoofed if it mixes ASCII with non-ASCII letters
    (e.g. "ignоre" with a Cyrillic о) or its non-ASCII letters are Latin
    variants (e.g. "ɑttɑck"). Words written entirely in another script
    ("привет", "日本語") are real text and are left alone.
    """
    def replace(m, chunk):
        word = m.group()
        foreign = [c for c in word if not c.isascii() and c.isalpha()]
        if not foreign:
            return None
        has_ascii = any(c.isascii() and c.isalpha() for c in word)
        if not has_ascii and not all(_script(c) == 'LATIN' for c in foreign):
            return None
        return [((_ascii_lookalike(c) or c) if not c.isascii() else c, s, e) for c, s, e in chunk]
    return _apply(chars, WORD_RE, replace)


# ---------------------------------------------------------------------------
# 3. evasion: separators, leetspeak, stretched letters, whitespace
# ---------------------------------------------------------------------------

LEET_MAP = {
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
    '7': 't', '8': 'b', '@': 'a', '$': 's', '!': 'i',
}
LEET_CHARS = re.escape(''.join(LEET_MAP))

# Three or more single letters/leet chars joined by separator noise: "i-g-n-o-r-e", "1 g n 0 r 3"
SEPARATED_RE = re.compile(
    rf'(?<![a-z{LEET_CHARS}])[a-z{LEET_CHARS}](?:[\s\-_.*|/+]{{1,3}}[a-z{LEET_CHARS}]){{2,}}(?![a-z{LEET_CHARS}])'
)
SEPARATOR_CHARS = set(' \t\n\r\f\v-_.*|/+')
TOKEN_RE = re.compile(rf'[a-z{LEET_CHARS}]+')
STRETCHED_RE = re.compile(r'([a-z])\1{2,}')
WHITESPACE_RE = re.compile(r'\s+')


def _collapse_separators(chars):
    def replace(m, chunk):
        return [t for t in chunk if t[0] not in SEPARATOR_CHARS]
    return _apply(chars, SEPARATED_RE, replace)


def _undo_leetspeak(chars):
    """Map leet digits/symbols to letters, only inside word-like tokens.

    A token needs at least two real letters ("1gn0r3", "@dm1n"), so numbers,
    prices, dates and phone numbers ("2024", "$4", "509-335-1234") are left
    alone. Trailing "!" is treated as punctuation, not an "i".
    """
    def replace(m, chunk):
        token = m.group()
        if sum(c.isalpha() for c in token) < 2:
            return None
        body = len(token.rstrip('!'))
        return [(LEET_MAP.get(c, c) if i < body else c, s, e) for i, (c, s, e) in enumerate(chunk)]
    return _apply(chars, TOKEN_RE, replace)


def _collapse_stretched(chars):
    """'ignooore' -> 'ignore'. The kept letter covers the whole original run."""
    def replace(m, chunk):
        return [(m.group(1), *_chunk_span(chunk))]
    return _apply(chars, STRETCHED_RE, replace)


def _collapse_whitespace(chars):
    def replace(m, chunk):
        return [(' ', *_chunk_span(chunk))]
    chars = _apply(chars, WHITESPACE_RE, replace)
    while chars and chars[0][0] == ' ':
        chars = chars[1:]
    while chars and chars[-1][0] == ' ':
        chars = chars[:-1]
    return chars


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

PIPELINE = [
    _decode_tag_chars,
    _decode_html_entities,
    _decode_url_escapes,
    _decode_base64,
    _drop_invisible,
    _fold,
    _map_homoglyphs,
    _collapse_separators,
    _undo_leetspeak,
    _collapse_stretched,
    _collapse_whitespace,
]


def normalize_with_map(text):
    """
    Normalize text for injection scanning and keep a map back to the original.

    Handles:
    - Hidden text: Unicode tag characters, HTML entities, URL escapes, base64
    - Invisible characters (zero-width, soft hyphen, BOM, bidi overrides)
    - Fullwidth / math-styled letters, case, accents (ｉｇｎｏｒｅ, IGNORE, ignóre -> ignore)
    - Homoglyphs in spoofed words (ignоre with Cyrillic о, ɑttɑck)
    - Separator noise ("i-g-n-o-r-e", "i g n o r e")
    - Leetspeak inside words ("1gn0r3"), but not in numbers
    - Stretched letters ("ignooore") and excess whitespace

    Returns a NormalizedText; use .text for scanning and .original_span()
    to find what to redact in the original.
    """
    chars = [(c, i, i + 1) for i, c in enumerate(text)]
    for stage in PIPELINE:
        chars = stage(chars)
    return NormalizedText(
        text=''.join(c for c, _, _ in chars),
        starts=[s for _, s, _ in chars],
        ends=[e for _, _, e in chars],
        original=text,
    )


def normalize_prompt(text):
    """Normalized text only, for callers that don't need the offset map."""
    return normalize_with_map(text).text
