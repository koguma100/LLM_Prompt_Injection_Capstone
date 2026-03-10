import re
import unicodedata

def normalize_prompt(text):
    """
    Normalize prompt text to collapse common evasion techniques.
    Returns a cleaned version for secondary pattern scanning.
    The original prompt_text is preserved on the Prompt object for sanitization output.
    
    Handles:
    - Unicode homoglyphs (e.g. ɑ → a, ｉｇｎｏｒｅ → ignore)
    - Repeated characters (e.g. "ignooore" → "ignore")
    - Separator noise between characters (e.g. "i-g-n-o-r-e", "i g n o r e" → "ignore")
    - Leetspeak digit substitutions (e.g. "1gnore", "ign0re")
    - Excess whitespace
    """
    # 1. Unicode normalization: collapses fullwidth, homoglyphs, accented variants
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # 2. Lowercase
    text = text.lower()

    # 3. Leet-speak digit substitutions
    leet_map = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '7': 't',
        '@': 'a',
        '$': 's',
    }
    text = ''.join(leet_map.get(c, c) for c in text)

    # 4. Collapse separator noise between single characters (e.g. "i-g-n-o-r-e" or "i g n o r e")
    # Matches patterns where individual chars are separated by spaces, dashes, dots, or underscores
    text = re.sub(r'\b([a-z])([\s\-_.]+[a-z])+\b', lambda m: re.sub(r'[\s\-_.]', '', m.group(0)), text)

    # 5. Collapse repeated characters (e.g. "ignooore" → "ignore")
    text = re.sub(r'(.)\1{2,}', r'\1', text)

    # 6. Normalize remaining whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text