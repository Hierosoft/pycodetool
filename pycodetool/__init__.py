#!/usr/bin/env python3
from __future__ import print_function
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


def get_verbosity():
    return verbosity


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


# syntax_error_fmt = "{path}:{row}:{column}: {message}"
syntax_error_fmt = 'File "{path}", line {row}, {column} {message}'
# ^ such as (Python-style, so readable by Geany):
'''
  File "/redacted/git/pycodetool/pycodetool/spec.py", line 336, in read_spec
'''


def set_syntax_error_fmt(fmt):
    global syntax_error_fmt
    syntax_error_fmt = fmt


def to_syntax_error(path, lineN, msg, col=None):
    '''
    Convert the error to a syntax error that specifies the file and line
    number that has the bad syntax.

    Keyword arguments:
    col -- is the character index relative to the start of the line,
        starting at 1 for compatibility with outputinspector (which will
        subtract 1 if using editors that start at 0).
    '''
    this_fmt = syntax_error_fmt

    if col is None:
        part = "{column}"
        removeI = this_fmt.find(part)
        if removeI > -1:
            suffixI = removeI + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:removeI] + this_fmt[suffixI:]
    if lineN is None:
        part = "{row}"
        removeI = this_fmt.find(part)
        if removeI > -1:
            suffixI = removeI + len(part) + 1
            # ^ +1 to get punctuation!
            this_fmt = this_fmt[:removeI] + this_fmt[suffixI:]
    return this_fmt.format(path=path, row=lineN, column=col, message=msg)
    # ^ Settings values not in this_fmt is ok.


def echo_SyntaxWarning(path, lineN, msg, col=None):
    msg = to_syntax_error(path, lineN, msg, col=col)
    echo0(msg)
    # ^ So the IDE can try to parse what path&line has an error.


def raise_SyntaxError(path, lineN, msg, col=None):
    echo_SyntaxWarning(path, lineN, msg, col=col)
    raise SyntaxError(msg)
