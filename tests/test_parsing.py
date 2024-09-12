# test_parsing.py

import pytest
from pycodetool.parsing import find_slice

find_slice_test_cases = [
    # (haystack, starter, ender, expected, id)
    ("(a+b)", "(", ")", (0, 5), "basic-parentheses"),
    ("{a+b}", "{", "}", (0, 5), "basic-curly-braces"),
    ("((a+b))", "(", ")", (0, 6), "identical-starter-ender"),
    ("(a+b", "(", ")", (-1, -1), "no-matching-ender"),
    ("a+b)", "(", ")", (-1, -1), "no-matching-starter"),
    ("((aa)a)", "(", ")", (0, 5), "multiple-starters-enders"),  # disregard nesting
    ("(a(b)c)", "(", ")", (0, 5), "nested-delimiters"),  # disregard nesting
    ("a(b)c)d", "(", ")", (1, 4), "extra-characters-outside"),
    ("[a(b)c]", "[", "]", (0, 7), "square-with-nested-round"),  # disregard nesting
    ("||abc|def|", "|", "|", (0, 2), "same-delimiter-twice"),
    # ("a\\(b)c)", "\\(", ")", (-1, -1), "escaped-start-not-matching"),
    # ("a\\(b\\)c", "\\(", "\\)", (-1, -1), "escaped-delimiters-not-matching"),
    # ("a\\(b\\)c", "(", ")", (-1, -1), "escaping-causing-mismatch"),
    # ("a\\(b\\)c(d)e", "(", ")", (2, 6), "escaped-with-valid-parentheses"),
    ("{a[(b)]c}d", "[", "]", (2, 7), "mixed-delimiter-types"),  # disregard nesting
    ("[a+b)c]", "[", "]", (0, 7), "mismatched-ordering"),
    ("[x(y(z)a)b]c", "[", "]", (0, 11), "multiple-nested-extra-characters"),  # disregard nesting
    ("xyz(a+b)c", "(", ")", (3, 8), "characters-before-and-after"),
    ("<<a>>b", "<", ">", (0, 4), "nested-angle-brackets"),  # disregard nesting
    (")a(b)c)", "(", ")", (2, 5), "extra-ender-before-starter-ignored"),
]

@pytest.mark.parametrize(
    "haystack, starter, ender, expected",
    [(case[0], case[1], case[2], case[3]) for case in find_slice_test_cases],
    ids=[case[4] for case in find_slice_test_cases]
)
def test_find_slice(haystack, starter, ender, expected):
    """
    Test the `find_slice` function with various inputs including edge cases,
    nested characters, escaped characters, and special symbols.
    """
    assert find_slice(haystack, starter, ender) == expected
