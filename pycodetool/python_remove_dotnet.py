# -*- coding: utf-8 -*-
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
for i in range(0, len(sys.argv)):
    if i == 0:
        print("  ignoring arg:" + sys.argv[i])
        continue
    arg = sys.argv[i]
    if arg != os.path.basename(__file__):
        args.append(arg)
        if len(args) == 1:
            print("  input file: " + arg)
if len(args) >= 2:
    print("  output file: " + args[1])
    if len(args) >= 3:
        print("  identifier list output file: " + arg[2])
    out_list_path = None
    if len(args) >= 3:
        out_list_path = os.path.realpath(args[2])
    parser = pct.PCTParser(args[0])
    parser.framework_to_standard_python(args[1])
    if out_list_path is not None:
        parser.save_identifier_lists(out_list_path)
else:
    print("")
    print("")
    print("  ERROR: missing destination (nothing done)")
    print("")
    print(__doc__)
    print("")
