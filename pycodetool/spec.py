# -*- coding: utf-8 -*-
import os
import sys

from pycodetool import (
    MODULE_DIR,
    REPO_DIR,
)
DOC_DEV_DIR = os.path.join(REPO_DIR, "doc", "development")
# TODO: ^ change to os.path.join(MODULE_DIR, "data")
CS_SPEC_PATH = os.path.join(DOC_DEV_DIR, "csharp-spec-5.0-grammar.txt")
grammar_tree = None
EXAMPLE_HTML = '''<!-- p. 476-510 (each separated by two newlines) from
<a href="https://www.microsoft.com/en-us/download/confirmation.aspx?
id=7029">C# Language Specification 5.0</a> by Microsoft -->
<!--set page=476-->
<pre>
<code>
</code>
</pre>
'''
# ^ deprecated HTML grammar
#   (where BNF lines are between <code> and </code>; I also changed
#   " opt" to "<sub>opt</sub>")
#   - I had added HTML to document the csharp grammar spec, but I've
#     reverted it back to the original text pasted from the spec. For
#     optional parts, I've changed " opt" to "_opt" (subscript notation
#     barrowed from LaTeX).

from .find_hierosoft import hierosoft
# ^ It changes sys.path so importing submodules below will even work.

from hierosoft.logging import (
    echo0,
    echo1,
    echo2,
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


def new_specdef(section, line, path, line_n, col=None, page_n=None):
    name = None
    positive_flag = ": one of"
    specdef = {
        'section': section,
        'line_n': line_n,
    }
    if page_n is not None:
        specdef['page_n'] = page_n
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
            line_n,
            ('new_specdef line must end with ":" or "{}" but got "{}"'
             ''.format(positive_flag, line)),
            col=col,
        )
    if name != name.rstrip():
        raise_SyntaxError(
            path,
            line_n,
            'new_specdef line has an unexpected space before ":"',
            col=col,
        )
    specdef['symbol'] = name.strip()
    return specdef


def is_unicode_char(statement, line_n=None):
    c, i = to_unicode_char(statement, no_exception=True)
    if c is not None:
        return True
    return False


def to_unicode_char(statement, no_exception=False, line_n=None):
    '''
    Keyword arguments:
    line_n -- the line number in the source code that caused the error.
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
                line_n,
                ('A unicode character should start',
                 ' with "{}" in human-readable spec'
                 ' format.'.format(opener)),
                col=None,
            )
    start = openerI + len(opener)
    closer = " )"
    closerI = statement.find(closer, start)
    if not statement.endswith(")"):
        if no_exception:
            return None, -1
        else:
            raise_SyntaxError(
                path,
                line_n,
                ('A unicode character starting',
                 ' with "{}" should end'
                 ' with "{}" in human-readable spec'
                 ' format.'.format(opener, closer)),
                col=None,
            )
    quad = statement[start:closerI]
    if len(quad) != 4:
        raise_SyntaxError(path, line_n,
                          ('A unicode character starting',
                           ' with "{}" and ending'
                           ' with "{}" should be 4 hex characters'
                           ' in human-readable spec'
                           ' format but is "{}".'
                           ''.format(opener, closer, quad)),
                          col=None)
    return ('\\u{}'.format(quad).decode('unicode_escape'), openerI)


def parse_spec_list(statement, path, line_n, col=None):
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
                line_n,
                ('The list is in an unknown format'
                 ' (expected "and " or "or " before "{}")'
                 ''.format(parts[-1])),
                col=col,
            )
    for i in range(len(parts)):
        if is_unicode_char(parts[i]):
            parts[i] = to_unicode_char(parts[i])
    return parts


def new_negative_charset(statement, path, line_n, col=None):
    if not statement.startswith(neg_charset_opener):
        raise_SyntaxError(
            path,
            line_n,
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


def get_tree_line_n_max():
    result = 0
    for section, specdefs in grammar_tree.items():
        for symbol, specdef in specdefs.items():
            line_n = specdef['line_n']
            if line_n > result:
                result = line_n
    return result


def get_specdef_at_line(index, no_exception=True):
    for section, specdefs in grammar_tree.items():
        for symbol, specdef in specdefs.items():
            line_n = specdef['line_n']
            if line_n == index:
                return specdef
    if no_exception is False:
        raise IndexError('There was no specdef defined on line {}'
                         ''.format(index))
    return None


def dump_specdefs():
    count = get_tree_line_n_max() + 1
    section = None
    prev_page_n = None
    page_n = None
    for i in range(count):
        specdef = get_specdef_at_line(i)
        if specdef is None:
            continue
        page_n = specdef.get('page_n')
        if page_n is not None:
            if page_n != prev_page_n:
                # echo1("page {} -> {}".format(prev_page_n, page_n))
                print("")

        if (section is None) or (specdef['section'] != section):
            section = specdef['section']
            print(section)
        suffix = ":"
        line_n = specdef['line_n']
        if specdef['is_value_list']:
            suffix = ": one of"
        print("    {}{}".format(specdef['symbol'], suffix))
        if 'encoded_values' in specdef:
            if not specdef['is_value_list']:
                raise RuntimeError(
                    to_syntax_error(
                        last_path,
                        line_n,
                        'encoded_values on wrong spec: {}'.format(len(specdef)),
                    )
                )
            e_values = specdef['encoded_values']
            if len(e_values) < 2:
                raise RuntimeError(
                    to_syntax_error(
                        last_path,
                        line_n,
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
                        line_n,
                        'got only {} encoded_options'.format(len(e_values)),
                    )
                )
            for value in e_values:
                print("        {}".format(value))
        else:
            raise RuntimeError(
                to_syntax_error(
                    last_path,
                    line_n,
                    'The members list key is unknown for: {}'.format(specdef),
                )
            )
        prev_page_n = page_n


def read_spec(path):
    global last_path
    # global specdefs
    global grammar_tree
    last_path = path
    line_n = 0
    specdef = None
    specdefs = None
    prev_page_n = None
    page_n = 476
    grammar_tree = {}
    with open(path, 'r') as ins:
        tab = "    "
        depth = 0
        prev_depth = 0
        value_depth = 2
        started = False
        section = None
        for rawL in ins:
            line_n += 1  # Counting numbers start at 1.
            line = rawL.rstrip()
            if line.strip() == "":
                prev_depth = depth
                if page_n is not None:
                    page_n += 1
                continue
            if not started:
                # deprecated, for html (see EXAMPLE_HTML variable)
                setter = "<!--set "
                setterI = line.find(setter)
                if setterI > -1:
                    startNameI = setterI + len(setter)
                    ender = "-->"
                    enderI = line.find(ender, startNameI)
                    if enderI > -1:
                        assignment = line[startNameI:enderI]
                        signI = assignment.find("=")
                        if signI > -1:
                            name = assignment[:signI]
                            value = assignment[signI+1:]
                            if name == "page":
                                page_n = int(value)
                                echo0('line {} set {}="{}"'
                                      ''.format(line_n, name, value))
                            else:
                                echo0('undefined parser variable name: "{}"'
                                      ''.format(name))
                        else:
                            echo2('no \'=\' in "{}"'
                                  ''.format(line))
                    else:
                        echo2('no "{}" in "{}"'
                              ''.format(ender, line))
                else:
                    echo2('no "{}" in "{}"'
                          ''.format(setter, line))

                # if "<code>" in line:
                if "B.1 Lexical grammar" in line:
                    started = True
                    section = line.strip()
                else:
                    echo0('* ignoring text before start: "{}"'.format(line))
                    prev_depth = depth
                    continue
            if page_n is not None:
                if page_n != prev_page_n:
                    echo1("page {} -> {}".format(prev_page_n, page_n))
            if "</code>" in line:
                # deprecated HTML format (See EXAMPLE_HTML variable)
                echo0(to_syntax_error(path, line_n,
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

            if depth == 0:
                section = line.strip()
                if section not in grammar_tree:
                    grammar_tree[section] = {}
                specdefs = grammar_tree[section]
            elif depth == 1:
                specdef = new_specdef(section, line, path, line_n,
                                      page_n=page_n)
                symbol = specdef['symbol']
                if symbol in specdefs:
                    oldN = specdefs[symbol]['line_n']
                    msg = to_syntax_error(
                        path,
                        line_n,
                        ('"{}" was already defined on line {}'
                         ''.format(symbol, oldN)),
                    )
                    echo0(msg)
                    echo_SyntaxWarning(
                        path,
                        oldN,
                        ('original definition (redefined on row {})'
                         ''.format(line_n)),
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
                            line_n,
                            ('The type of values expected is unknown.'
                             ''.format(symbol, oldN)),
                        )
                    )
                pass
            prev_depth = depth
            prev_page_n = page_n


def main():
    path = CS_SPEC_PATH
    read_spec(path)
    dump_specdefs()
    return 0


if __name__ == "__main__":
    sys.exit(main())
