import re
import unicodedata
from confusables import confusable_characters

# Normalize homoglyphs to their ASCII equivalents where possible, otherwise keep original character
def normalize_homoglyphs(text):
    result = []
    for char in text:
        # skip ASCII characters
        if char.isascii():
            result.append(char)
            continue

        confusable = confusable_characters(char)
        if confusable:
            # confusable_characters returns a list of characters this could be confused with
            # pick the ASCII one if available, otherwise keep original
            ascii_version = next((c for c in confusable if c.isascii()), None)
            result.append(ascii_version if ascii_version else char)
        else:
            result.append(char)
    return ''.join(result)

def normalize_prompt(text):
    """
    Normalize prompt text to collapse common evasion techniques.
    Returns a cleaned version for secondary pattern scanning.
    To be used first and foremost. The original prompt_text is preserved on the Prompt object for sanitization output.

    Handles:
    - Unicode homoglyphs (e.g. ɑ → a, ｉｇｎｏｒｅ → ignore)
    - Repeated characters (e.g. "ignooore" → "ignore")
    - Separator noise between characters (e.g. "i-g-n-o-r-e", "i g n o r e" → "ignore")
    - Leetspeak digit substitutions (e.g. "1gnore", "ign0re")
    - Excess whitespace
    """
    # 1. Remove zero-width and invisible characters that could be used for obfuscation
    text = re.sub(r'[\u200b\u200c\u200d\u00ad\ufeff]', '', text)

    # 2. NFKD first — handles fullwidth characters (ｉ→i, ａ→a etc.)
    text = unicodedata.normalize('NFKD', text)

    # 3. Homoglyph normalization — only needed for non-ASCII that survived NFKD
    text = normalize_homoglyphs(text)

    # 4. Drop any remaining non-ASCII that couldn't be mapped
    text = text.encode('ascii', 'ignore').decode('ascii')

    # 5. Lowercase
    text = text.lower()
    print(text)

    # 6. Leet-speak digit substitutions
    leet_map = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '7': 't',
        '@': 'a',
        '$': 's',
        '8': 'b',
        '!': 'i',
    }
    text = ''.join(leet_map.get(c, c) for c in text)

    # 7. Collapse separator noise between single characters (e.g. "i-g-n-o-r-e" or "i g n o r e")
    # Matches patterns where individual chars are separated by spaces, dashes, dots, or underscores
    text = re.sub(r'\b([a-z])([\s\-_.]+[a-z])+\b', lambda m: re.sub(r'[\s\-_.]', '', m.group(0)), text)

    # 8. Collapse repeated characters (e.g. "ignooore" → "ignore")
    text = re.sub(r'(.)\1{2,}', r'\1', text)

    # 9. Normalize remaining whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

