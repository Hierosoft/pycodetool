#!/usr/bin/env python3
from __future__ import print_function
import sys
import os

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
DATA_DIR = os.path.join(MODULE_DIR, "data")

from .find_hierosoft import hierosoft

from hierosoft.logging import (
    get_verbosity,
    set_verbosity,
    echo0,
    echo1,
    echo2,
    echo3,
    set_syntax_error_fmt,
    to_syntax_error,
    echo_SyntaxWarning,
    raise_SyntaxError,
)
