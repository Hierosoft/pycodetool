#!/usr/bin/env python3

import sys

python_mr = sys.version_info[0]

verbosity = 0
for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if arg.startswith("--"):
        if arg == "--verbosity":
            verbosity = 1
        elif arg == "--debug":
            verbosity = 2


def set_verbosity(level):
    global verbosity
    verbosity_levels = [True, False, 0, 1, 2]
    if level not in verbosity_levels:
        raise ValueError("verbosity must be 0-2 but was {}".format(verbosity))
    verbosity = level


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def echo1(*args, **kwargs):
    if not verbosity:
        return
    print(*args, file=sys.stderr, **kwargs)


def echo2(*args, **kwargs):
    if verbosity < 2:
        return
    print(*args, file=sys.stderr, **kwargs)


def echo3(*args, **kwargs):
    if verbosity < 3:
        return
    print(*args, file=sys.stderr, **kwargs)


def to_syntax_error(path, lineN, msg, col=None):
    '''
    Convert the error to a syntax error that specifies the file and line
    number that has the bad syntax.

    Keyword arguments:
    col -- is the character index relative to the start of the line,
        starting at 1 for compatibility with outputinspector (which will
        subtract 1 if using editors that start at 0).
    '''
    if lineN is not None:
        if col is not None:
            return "{}:{}:{}: {}".format(path, lineN, col, msg)
        return "{}:{}: {}".format(path, lineN, msg)
    return "{}: {}".format(path, msg)
