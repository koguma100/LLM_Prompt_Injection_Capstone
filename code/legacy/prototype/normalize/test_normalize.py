import pytest
from normalize_fuzzy import normalize_prompt

# --- Unicode Normalization ---
def test_fullwidth_characters():
    assert normalize_prompt("ｉｇｎｏｒｅ") == "ignore"

def test_accented_characters():
    assert normalize_prompt("café") == "cafe"

def test_homoglyph_characters():
    # ɑ (latin alpha) → a
    assert normalize_prompt("ɑttɑck") == "attack"

# --- Lowercase ---
def test_uppercase_input():
    assert normalize_prompt("IGNORE THIS") == "ignore this"

def test_mixed_case_input():
    assert normalize_prompt("IgNoRe ThIs") == "ignore this"

# --- Leetspeak ---
def test_leet_zeros():
    assert normalize_prompt("ign0re") == "ignore"

def test_leet_ones():
    assert normalize_prompt("1gnore") == "ignore"

def test_leet_at_sign():
    assert normalize_prompt("@ttack") == "attack"

def test_leet_dollar_sign():
    assert normalize_prompt("$ystem") == "system"

def test_leet_multiple_substitutions():
    assert normalize_prompt("@dm1n 4cc3ss") == "admin access"

# --- Separator Noise ---
def test_dash_separated_chars():
    assert normalize_prompt("i-g-n-o-r-e") == "ignore"

def test_space_separated_chars():
    assert normalize_prompt("i g n o r e") == "ignore"

def test_dot_separated_chars():
    assert normalize_prompt("i.g.n.o.r.e") == "ignore"

def test_underscore_separated_chars():
    assert normalize_prompt("i_g_n_o_r_e") == "ignore"

# --- Repeated Characters ---
def test_triple_repeated_chars():
    assert normalize_prompt("ignooore") == "ignore"

def test_many_repeated_chars():
    assert normalize_prompt("ignooooooore") == "ignore"

def test_double_repeated_chars_unchanged():
    # Only 3+ repetitions are collapsed
    assert normalize_prompt("ignoore") == "ignoore"

# --- Whitespace ---
def test_excess_whitespace_collapsed():
    assert normalize_prompt("ignore   this") == "ignore this"

def test_leading_trailing_whitespace():
    assert normalize_prompt("  ignore this  ") == "ignore this"

def test_tab_whitespace():
    assert normalize_prompt("ignore\tthis") == "ignore this"

# --- Combined Evasion ---
def test_leet_plus_separators():
    assert normalize_prompt("1-g-n-0-r-3") == "ignore"

def test_fullwidth_plus_repeated():
    assert normalize_prompt("ｉｇｎｏｏｏｒｅ") == "ignore"

def test_mixed_evasion():
    assert normalize_prompt("  1GN0R3   tH!$  ") == "ignore this"  # ! has no mapping

# --- Edge Cases ---
def test_empty_string():
    assert normalize_prompt("") == ""

def test_plain_text_unchanged():
    assert normalize_prompt("hello world") == "hello world"

def test_single_character():
    assert normalize_prompt("A") == "a"