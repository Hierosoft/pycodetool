# -*- coding: utf-8 -*-
import unittest
import sys
import os

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

from pycodetool import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
    to_syntax_error,
)


class TestLogging(unittest.TestCase):
    def test_to_syntax_error(self):
        self.assertEqual(
            to_syntax_error("no_file", None, "no_error"),
            "no_file: no_error",
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error"),
            "no_file:3: no_error",
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error", col=4),
            "no_file:3:4: no_error",
        )


if __name__ == "__main__":
    testcase = TestLogging()
    for name in dir(testcase):
        if name.startswith("test"):
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here