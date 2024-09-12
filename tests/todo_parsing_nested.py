# test_parsing.py

import pytest
from pycodetool.parsing import find_slice

test_cases = [
    # FIXME: Test data needs to be reviewed.
    # (haystack, starter, ender, expected, id)
    ("(a+b)", "(", ")", (0, 5), "basic-parentheses"),
    ("{a+b}", "{", "}", (0, 5), "basic-curly-braces"),
    ("((a+b))", "(", ")", (0, 6), "identical-starter-ender"),
    ("(a+b", "(", ")", (-1, -1), "no-matching-ender"),
    ("a+b)", "(", ")", (-1, -1), "no-matching-starter"),
    ("((aa)a)", "(", ")", (0, 5), "multiple-starters-enders"),
    ("(a(b)c)", "(", ")", (0, 7), "nested-delimiters"),
    ("a(b)c)d", "(", ")", (1, 4), "extra-characters-outside"),
    ("[a(b)c]", "[", "]", (0, 7), "square-with-nested-round"),
    ("||abc|def|", "|", "|", (0, 4), "same-delimiter-twice"),
    ("a\\(b)c)", "\\(", ")", (-1, -1), "escaped-start-not-matching"),
    ("a\\(b\\)c", "\\(", "\\)", (-1, -1), "escaped-delimiters-not-matching"),
    ("a\\(b\\)c", "(", ")", (-1, -1), "escaping-causing-mismatch"),
    ("a\\(b\\)c(d)e", "(", ")", (6, 9), "escaped-with-valid-parentheses"),
    ("{a[(b)]c}d", "[", "]", (3, 6), "mixed-delimiter-types"),
    ("[a+b)c]", "[", "]", (0, 6), "mismatched-ordering"),
    ("[x(y(z)a)b]c", "[", "]", (0, 11), "multiple-nested-extra-characters"),
    ("xyz(a+b)c", "(", ")", (3, 8), "characters-before-and-after"),
    ("<<a>>b", "<", ">", (0, 3), "nested-angle-brackets"),
    (")a(b)c)", "(", ")", (2, 5), "extra-ender-before-starter-ignored"),  # New test case
]

@pytest.mark.parametrize(
    "haystack, starter, ender, expected",
    [(case[0], case[1], case[2], case[3]) for case in test_cases],
    ids=[case[4] for case in test_cases]
)
def test_find_slice(haystack, starter, ender, expected):
    """
    Test the `find_slice` function with various inputs including edge cases,
    nested characters, escaped characters, and special symbols.
    """
    assert find_slice(haystack, starter, ender) == expected
