#!/usr/bin/env python
"""
bash2python
-----------
Purpose: Translate Bash to Python better than bash2py, by not eating
code nor assuming indentation determines correct Python scope.

Usage:
python3 bash2python.py <bash_script_path>
"""
import sys
import os
import re  # regex
import platform
import bashlex

if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

bash_to_python_header = """#!/usr/bin/env python3
import sys
import os
# import re  # regex

if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']

"""

def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def usage():
    echo0(__doc__)


class BashToPyTranslator:
    """Convert Bash syntax to Python
    """
    def __init__(self):
        self._streamCloseMark = None
        self.scopeLineStack = []
        self._streamName = None

    def translate(self, path):
        print(bash_to_python_header)
        with open(path, 'r') as stream:
            self._translate(path, stream)

    def _setCloseMark(self, closeMark, streamName):
        self._streamCloseMark = closeMark
        self._streamName = streamName

    def stringToSymbol(self, encodedString):
        sn = arg.replace("$", "").replace('"', '').replace("'", "")
        sn = sn.replace(" ", "").replace("\t", "")
        sn = sn.replace("\\", "")
        sn = sn.replace("/", "")
        return "_%s_stream" % sn.strip()

    def pushScope(self, opener):
        self.scopeLineStack.append(opener)

    def popScope(self):
        return self.scopeLineStack.pop()

    def scopeDepth(self):
        return len(self.scopeLineStack)

    def pyIndent(self):
        return "    " * self.scopeDepth()

    def _translate_line(self, path, stream, line, lineN, enable_rstrip=True):
        raise NotImplementedError("_translate_line")
        return self.pyIndent()+line

    def _translate(self, path, stream):
        lineN = 0
        for rawL in stream:
            lineN += 1
            line = self._translate_line(path, stream, rawL, lineN)
            print(line)


class DeprecatedBashToPyTranslator(BashToPyTranslator):
    """Convert some bash syntax to Python
    Deprecated: doesn't respect escaped quotes. Use bashlex instead.

    Attributes:
        _streamCloseMark (string): If not None, a file is open and this
            string at the beginning of a line closes it.
    """
    def __init__(self):
        streamAppendQuotedRE = re.compile(r'cat\s*>>\s*"')
        streamOpenQuotedRE = re.compile(r'cat\s*>\s*"')
        streamOpenEndQuotedRE = re.compile(r'"\s*<<')
        # ^ assumes not still inside quotes!
        streamAppendRE = re.compile(r'cat\s*>>\s*')
        streamOpenRE = re.compile(r'cat\s*>\s*')
        streamOpenEndRE = re.compile(r'\s*<<')
        # ^ assumes not still inside quotes!
        self.streamEnclosureRegexes = [
            [streamAppendQuotedRE, streamOpenEndQuotedRE],
            [streamOpenQuotedRE, streamOpenEndQuotedRE],
            [streamAppendRE, streamOpenEndRE],
            [streamOpenRE, streamOpenEndRE],
        ]

        self._streamCloseMark = None
        self.scopeLineStack = []
        self._streamName = None

    def _translate_line(self, path, stream, line, lineN, enable_rstrip=True):
        if enable_rstrip:
            line = line.rstrip()
        indent_len = len(line) - len(line.lstrip())
        # _old_unused_indent = line[:indent_len]
        if self._streamName is not None:
            # If a stream is open
            # See if it is closed on this line:
            if line.rstrip() == self._streamCloseMark:
                self._streamCloseMark = None
                # end the "with" statement
                oldOpener = popScope()
                # ^ changes result of pyIndent() appropriately
            else:
                return self.pyIndent()+'%s.write("%s\\n")' % (
                    self._streamName,
                    line.replace('\t', "\\t").replace('"', '\\"')
                )
        else:
            openEndRE = None
            mode = 'w'
            for pair in self.streamEnclosureRegexes:
                openRE, closeRE = pair
                openMatch = openRE.search(line)
                if openMatch is None:
                    continue
                closeMatch = closeRE.search(line, openMatch.span()[1])
                # ^ .span()[1] to start after previous match slice
                if closeMatch is None:
                    raise ValueError(
                        'File "%s", line %s: could not detect'
                        ' stream end mark definition after %s'
                        % (path, lineN, openRE.pattern)
                    )
                arg = line[openMatch.span()[1]:closeMatch.span()[0]]
                closeMark = line[closeMatch.span()[1]:].strip()
                streamName = self.stringToSymbol(arg)
                self._setCloseMark(closeMark, streamName)
                self.pushScope(line)
                return self.pyIndent()+'with open (%s) as %s:' % (arg, streamName)

        line = line.lstrip()
        redirectS = ">>"
        echoS = "echo "
        echoAndQuote = 'echo "'
        if line.startswith(echoAndQuote):
            valueI = len(echoAndQuote) - 1  # - 1 to keep the double quote
            endI = line.find('"', 6)
            redirectI = line.find(redirectS, 6)
            if endI < 0:
                raise ValueError(
                    'File "%s", line %s: Unclosed double quote' % (path, lineN)
                )
            # FIXME: find unquoted only (may have another quote!)
            inputStr = line[valueI:endI+1]  # +1 to include closing quote
            if redirectI > endI:
                rightI = redirectI+len(redirectS)
                streamName = line[rightI:]
                if not streamName.startswith("$"):
                    raise ValueError(
                        'File "%s", line %s: unknown stream format: %s'
                        % (path, lineN, line)
                    )
                line = '%s.write(%s+"\\n")' % (streamName, inputStr)
            else:
                line = 'print(%s)' % (inputStr)
        elif line.startswith(echoS):
            valueI = len(echoAndQuote)  # skip past space
            inputStr = line[valueI:].strip()
            if inputStr.startswith("$"):
                inputStr = inputStr[1:]
            line = 'print(%s)' % (inputStr)

        return self.pyIndent()+line


def main():
    if len(sys.argv) < 2:
        TRY_EM = os.path.join(HOME, "git", "EnlivenMinetest")
        if os.path.isdir(TRY_EM):
            usage()
            print("Error: You must specify a file.", file=sys.stderr)
            src = os.path.join(TRY_EM, "utilities", "extra",
                               "install-ENLIVEN-minetest_game.sh")
            echo0("- running detected test file instead: %s" % src)
            return 0
        return 1
    if len(sys.argv) > 2:
        usage()
        print("Error: You must specify only one file.", file=sys.stderr)
        return 1
    path = sys.argv[1]
    if not os.path.isfile(path):
        usage()
        print("Error: %s does not exist." % repr(path), file=sys.stderr)
        return 1
    unbash = BashToPyTranslator()
    nameNoExt, dotExt = os.path.splitext(path)
    dstPath = nameNoExt + ".py"
    unbash.translate(path)
    echo0("")
    return 0

if __name__ == "__main__":
    sys.exit(main())
