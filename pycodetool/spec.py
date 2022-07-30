#!/usr/bin/env python3
import os
import sys

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
DATA_DIR = os.path.join(REPO_DIR, "doc", "development")
# TODO: ^ change to os.path.join(MODULE_DIR, "data")
CS_SPEC_PATH = os.path.join(DATA_DIR, "csharp-spec-5.0-grammar.html")
grammar_tree = None

try:
    import pycodetool
except ImportError as ex:
    # ^ Python 3 ModuleNotFoundError is a subclass of ImportError
    if (("No module named 'pycodetool'" in str(ex))  # Python 3
            or ("No module named pycodetool" in str(ex))):
        good_flag = os.path.join(REPO_DIR, "pycodetool", "__init__.py")
        if os.path.isfile(good_flag):
            sys.path.insert(0, REPO_DIR)
        else:
            sys.stderr.write('There is no "{}"\n'.format(good_flag))
            sys.stderr.flush()
            raise ex
    else:
        raise ex


from pycodetool import (
    echo0,
    to_syntax_error,
    raise_SyntaxError,
    echo_SyntaxWarning,
)

char_classes = [
    "A unicode character",
    "Any character with Unicode class"
]
class_keywords = [
    "of classes",
    "of the class",
    "representing a character of the class",
    "representing a character of classes",
]
'''
unicode_chars = [
    "Horizontal tab character ( U+0009 )" = '\\u0009'.decode('unicode_escape'),
    "Vertical tab character ( U+0009 )" = '\\u000b'.decode('unicode_escape'),
    "Form feed character ( U+0009 )" = '\\u000c'.decode('unicode_escape'),
]
'''

neg_charset_opener = "Any character except "
last_path = None


def new_specdef(section, line, path, lineN, col=None):
    name = None
    positive_flag = ": one of"
    specdef = {
        'section': section,
        'line_num': lineN,
    }
    if line.endswith(positive_flag):
        specdef['positive'] = True
        specdef['is_value_list'] = True
        specdef['encoded_values'] = []
        name = line[:-len(positive_flag)]
    elif line.endswith(":"):
        specdef['positive'] = True
        specdef['is_value_list'] = False
        specdef['encoded_options'] = []
        name = line[:-1]
    else:
        raise_SyntaxError(
            path,
            lineN,
            ('new_specdef line must end with ":" or "{}" but got "{}"'
             ''.format(positive_flag, line)),
            col=col,
        )
    if name != name.rstrip():
        raise_SyntaxError(
            path,
            lineN,
            'new_specdef line has an unexpected space before ":"',
            col=col,
        )
    specdef['symbol'] = name.strip()
    return specdef


def is_unicode_char(statement, lineN=None):
    c, i = to_unicode_char(statement, no_exception=True)
    if c is not None:
        return True
    return False


def to_unicode_char(statement, no_exception=False, lineN=None):
    '''
    Keyword arguments:
    lineN -- the line number in the source code that caused the error.
    no_exception -- return None instead of raising an exception if not
        a unicode character specifier (but still raise an exception if
        is one that isn't in the right format).

    Returns:
    (1-character-long str or None, Index or -1)
    '''
    opener = " ( U+"
    openerI = statement.find(opener)
    if openerI < 0:
        if no_exception:
            return None, -1
        else:
            raise_SyntaxError(
                path,
                lineN,
                ('A unicode character should start',
                 ' with "{}" in human-readable spec'
                 ' format.'.format(opener)),
                col=None,
            )
    start = openerI + len(opener)
    closer = " )"
    closerI = statement.find(closer, start=start)
    if not statement.endswith(")"):
        if no_exception:
            return None, -1
        else:
            raise_SyntaxError(
                path,
                lineN,
                ('A unicode character starting',
                 ' with "{}" should end'
                 ' with "{}" in human-readable spec'
                 ' format.'.format(opener, closer)),
                col=None,
            )
    quad = statement[start:closerI]
    if len(quad) != 4:
        raise_SyntaxError(path, lineN,
                          ('A unicode character starting',
                           ' with "{}" and ending'
                           ' with "{}" should be 4 hex characters'
                           ' in human-readable spec'
                           ' format but is "{}".'
                           ''.format(opener, closer, quad)),
                          col=None)
    return ('\\u{}'.format(quad).decode('unicode_escape'), openerI)


def parse_spec_list(statement, path, lineN, col=None):
    parts = statement.split(",")
    for i in range(len(parts)):
        parts[i] = parts[i].strip()
    if len(parts) > 1:
        if parts[-1].startswith("and "):
            parts[-1] = parts[-1][4:].strip()
        elif parts[-1].startswith("or "):
            parts[-1] = parts[-1][4:].strip()
        else:
            raise_SyntaxError(
                path,
                lineN,
                ('The list is in an unknown format'
                 ' (expected "and " or "or " before "{}")'
                 ''.format(parts[-1])),
                col=col,
            )
    for i in range(len(parts)):
        if is_unicode_char(parts[i]):
            parts[i] = to_unicode_char(parts[i])
    return parts


def new_negative_charset(statement, path, lineN, col=None):
    if not statement.startswith(neg_charset_opener):
        raise_SyntaxError(
            path,
            lineN,
            ('new_negative_charset statement must start with "{}"'
             ''.format(neg_charset_opener)),
            col=col,
        )
    value_str = statement[len(neg_charset_opener):]
    return {
        'characters': parse_spec_list(value_str),
        'positive': False,
    }


# Example of ['positive'] definition in grammar spec:
# Any character except " ( U+0022 ), \ ( U+005C ), and new-line-character
def is_in_charset(needle, charset):
    if len(needle) > 1:
        raise ValueError("is_in_character_set accepts only one character.")
    if not charset['positive']:
        return needle not in charset['characters']
    return needle in charset['characters']


def count_specdef_lines():
    count = 0
    for section, specdefs in grammar_tree.items():
        for symbol, specdef in specdefs.items():
            lineN = specdef['line_num']
            if lineN > count:
                count = lineN  # correct since starting at 1
    return count


def get_specdef_at_line(index, no_exception=True):
    for section, specdefs in grammar_tree.items():
        for symbol, specdef in specdefs.items():
            lineN = specdef['line_num']
            if lineN == index:
                return specdef
    if no_exception is False:
        raise IndexError('There was no specdef defined on line {}'
                         ''.format(index))
    return None


def dump_specdefs():
    count = count_specdef_lines()
    section = None
    for i in range(count):
        specdef = get_specdef_at_line(i)
        if specdef is None:
            continue
        if (section is None) or (specdef['section'] != section):
            section = specdef['section']
            print(section)
        suffix = ":"
        lineN = specdef['line_num']
        if specdef['is_value_list']:
            suffix = ": one of"
        print("    {}{}".format(specdef['symbol'], suffix))
        if 'encoded_values' in specdef:
            if not specdef['is_value_list']:
                raise RuntimeError(
                    to_syntax_error(
                        last_path,
                        lineN,
                        'encoded_values on wrong spec: {}'.format(len(specdef)),
                    )
                )
            e_values = specdef['encoded_values']
            if len(e_values) < 2:
                raise RuntimeError(
                    to_syntax_error(
                        last_path,
                        lineN,
                        'got only {} encoded_values'.format(len(e_values)),
                    )
                )
            for value in e_values:
                print("        {}".format(value))
        elif 'encoded_options' in specdef:
            e_values = specdef['encoded_options']
            if len(e_values) < 1:
                raise RuntimeError(
                    to_syntax_error(
                        last_path,
                        lineN,
                        'got only {} encoded_options'.format(len(e_values)),
                    )
                )
            for value in e_values:
                print("        {}".format(value))
        else:
            raise RuntimeError(
                to_syntax_error(
                    last_path,
                    lineN,
                    'The members list key is unknown for: {}'.format(specdef),
                )
            )


def read_spec(path):
    global last_path
    # global specdefs
    global grammar_tree
    last_path = path
    lineN = 0
    specdef = None
    specdefs = None
    grammar_tree = {}
    with open(path, 'r') as ins:
        tab = "    "
        depth = 0
        prev_depth = 0
        value_depth = 2
        started = False
        section = None
        for rawL in ins:
            lineN += 1  # Counting numbers start at 1.
            line = rawL.rstrip()
            if line.strip() == "":
                prev_depth = depth
                continue
            if not started:
                # if "<code>" in line:
                if "B.1 Lexical grammar" in line:
                    started = True
                    section = line.strip()
                prev_depth = depth
                continue
            if "</code>" in line:
                echo0(to_syntax_error(path, lineN,
                                      "</code> ended (OK presumably)."))
                break
            stripped = line
            depth = 0
            while stripped.startswith(tab):
                depth += 1
                stripped = stripped[len(tab):]
            if stripped.startswith("\t"):
                raise SyntaxError(
                    "Only spaces are expected for indents."
                )
            if stripped.startswith(" "):
                raise SyntaxError(
                    "Only groups of 4 spaces are expected for indents."
                )
            if section not in grammar_tree:
                grammar_tree[section] = {}
            specdefs = grammar_tree[section]

            if depth == 0:
                section = line.strip()
            elif depth == 1:
                specdef = new_specdef(section, line, path, lineN)
                symbol = specdef['symbol']
                if symbol in specdefs:
                    oldN = specdefs[symbol]['line_num']
                    msg = to_syntax_error(
                        path,
                        lineN,
                        ('"{}" was already defined on line {}'
                         ''.format(symbol, oldN)),
                    )
                    echo0(msg)
                    echo_SyntaxWarning(
                        path,
                        oldN,
                        ('original definition (redefined on row {})'
                         ''.format(lineN)),
                    )
                specdefs[symbol] = specdef
                # print(depth*"   "+symbol)
            elif depth == 2:
                # specdef should always be defined by now (at a lower
                #   level of indentation).
                if specdef['is_value_list']:
                    specdef['encoded_values'].append(line.strip())
                elif specdef['is_value_list'] is False:
                    specdef['encoded_options'].append(line.strip())
                else:
                    raise RuntimeError(
                        to_syntax_error(
                            path,
                            lineN,
                            ('The type of values expected is unknown.'
                             ''.format(symbol, oldN)),
                        )
                    )
                pass
            prev_depth = depth

    dump_specdefs()


def main():
    path = CS_SPEC_PATH
    read_spec(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
