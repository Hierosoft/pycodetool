#!/usr/bin/env python
"""
usage:
  python_remove_dotnet.py <source> <dest> [<output identifierlist>]

example:
  python_remove_dotnet.py fromCSharpRequiresDotNet.py \
      fromCSharpStandardPython.py \"last run - identifiers.txt\""
"""

import sys
import os
import pct

args = list()
print("I am "+os.path.basename(__file__))
for arg in sys.argv:
    if arg != os.path.basename(__file__):
        args.append(arg)
        if len(args) == 1:
            print("  input file: "+arg)
    else:
        print("  ignoring arg:"+arg)
if len(args) >= 2:
    print("  output file: "+arg[1])
    if len(args) >= 3:
        print("  identifier list output file: "+arg[2])
    parser = pct.PCTParser(args[0])
    parser.framework_to_standard_python(args[1])
    if len(args) >= 3:
        parser.save_identifier_lists(args[2])
else:
    print("")
    print("")
    print("  ERROR: missing destination (nothing done)")
    print("")
    print(__doc__)
    print("")
