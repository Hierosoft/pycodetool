import os
import platform

from pycodetool import pct

from pycodetool.parsing import (
    assertEqual,
    assertAllEqual,
    quoted_slices,
    set_verbose,
    get_quoted_slices_error,
    which_slice,
    END_BEFORE_QUOTE_ERR,
    in_any_slice,
)

profile = None
AppDatas = None

if platform.system() == "Windows":
    profile = os.environ.get("USERPROFILE")
    if profile is None:
        print("ERROR: You must set USERPROFILE in Windows.")
        exit(1)
    AppDatas = os.path.join(profile, "AppData", "Roaming")
else:
    profile = os.environ.get("HOME")
    if profile is None:
        print("ERROR: You must set HOME in a non-Windows platform.")
        exit(1)
    AppDatas = os.path.join(profile, ".config")

Documents = os.path.join(profile, "Documents")
AppData = os.path.join(AppDatas, "pycodetool")
testOutDir = os.path.join(Documents, "pycodetool")

if not os.path.isdir(testOutDir):
    os.makedirs(testOutDir)

found_dir = None
try_dirs = []
ba = os.path.join(profile, "Documents", "GitHub", "blockability")
if not os.path.isdir(ba):
    ba = os.path.join(profile, "git", "blockability")

test_data_dir = os.path.join("tests", "data")
try_dirs.append(test_data_dir)
test_data_dir_i = len(try_dirs) - 1

try_dirs.append(ba)


from pycodetool.parsing import (
    find_unquoted_not_commented_not_parenthetical
)

found = find_unquoted_not_commented_not_parenthetical(
    "x = (i + a) + b # a",
    "a",
)
assertEqual(found, -1)


good_i = 14
found = find_unquoted_not_commented_not_parenthetical(
    "x = (i + a) + a # a",
    #              ^ for the test, good_s must be at good_i
    "a",
)
assertEqual(found, good_i)

good_i = 14
found = find_unquoted_not_commented_not_parenthetical(
    "x = (i + a) + a # a",
    #              ^ for the test, good_s must be at good_i
    "a",
    step=-1,  # Ensure a commented good_s is skipped by going in reverse
)
assertEqual(found, good_i)

set_verbose(True)

good_i = 20
found = find_unquoted_not_commented_not_parenthetical(
    "x = 'a' + (i + a) + a # a",
    #                    ^ for the test, this index must match good_i
    "a",
)
assertEqual(found, good_i, tbs=("find a non-quoted non-parenthetical"
                                " string after other matches that are"))

good_i = 20
good_s = "a"
test_s = 'x = "a" + (i + a) + a # a'
#                             ^ for the test, good_s must be at good_i
assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
            tbs="The test itself is wrong: good_s is not at good_i")
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
)
assertEqual(
    found,
    good_i,
    tbs="finding a non-quoted non-parenthetical string",
)

test_s = 'x = \\"a" + (i + a) + \"a\" # a'
good_i = -1
good_s = "a"
# assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
#             tbs="The test itself is wrong: good_s is not at good_i")
# ^ don't check since good_i is -1 (not found is correct)
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
)
assertEqual(found, good_i, tbs=("should find nothing since a backslash"
                                " outside of quotes doesn't count"))

test_s = 'x = "\\"" + a + (i + a) + \"a\" # a'
good_i = 11
good_s = "a"
assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
            tbs="The test itself is wrong: good_s is not at good_i")
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
)
assertEqual(found, good_i, tbs="finding the first escaped string")

test_s = 'x = \'\\\'\' + a + (i + a) + \"a\" # a'
good_i = 11
good_s = "a"
assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
            tbs="The test itself is wrong: good_s is not at good_i")
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
)
assertEqual(found, good_i, tbs=("finding the first escaped string with"
                                " an escaped quote"))

test_s = 'x = \'\\\'a\' + (i + a) + \"a\" # a'
good_i = 17
good_s = "a"
assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
            tbs="The test itself is wrong: good_s is not at good_i")
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
    step=-1,
)
assertEqual(found, good_i, tbs="finding the last escaped string")

# intentionally provide bad syntax to ensure the escape character is
# ignored when not in quotes:
test_s = 'x = \\"a" + (i + a) + \\"a\" # a'
good_i = 6
good_s = "a"
assertEqual(good_s, test_s[good_i:good_i+len(good_s)],
            tbs="The test itself is wrong: good_s is not at good_i")
found = find_unquoted_not_commented_not_parenthetical(
    test_s,
    good_s,
    step=-1,
)
assertEqual(found, good_i, tbs=("finding the last escaped string after"
                                " another escaped string"))

# intentionally botch the results by starting after the opening quote:
test_s = 'x = "a" + (i + a) + "a" # "a"'
goodIs = [(6, 21), (22, 27)]
assertEqual(test_s[goodIs[0][0]:goodIs[0][1]], '" + (i + a) + "',
            tbs="The silent degradation test itself is wrong.")
assertEqual(test_s[goodIs[1][0]:goodIs[1][1]], '" # "',
            tbs="The silent degradation test itself is wrong.")
gotIs = quoted_slices(test_s, start=6)
assertAllEqual(goodIs, gotIs, tbs=("quoted slices {} should silently"
                                   " degrade to {}"
                                   "".format(gotIs, goodIs)))
assertEqual(get_quoted_slices_error(), END_BEFORE_QUOTE_ERR)

test_s = 'x = "a" + (i + a) + "a" # "a"'
goodIs = [(4, 7), (20, 23)]
assertEqual(test_s[goodIs[0][0]:goodIs[0][1]], '"a"',
            tbs="The test itself is wrong.")
assertEqual(test_s[goodIs[1][0]:goodIs[1][1]], '"a"',
            tbs="The test itself is wrong.")
gotIs = quoted_slices(test_s)
assertAllEqual(goodIs, gotIs, tbs=("quoted slices {} should be {}"
                                   "".format(gotIs, goodIs)))
assertEqual(get_quoted_slices_error(), None)


goodIs = [(4, 6), (20, 22)]

w_slice = which_slice(21, goodIs)
assertEqual(w_slice, 1)
a_slice = in_any_slice(21, goodIs)
assertEqual(a_slice, True)

w_slice = which_slice(5, goodIs)
assertEqual(w_slice, 0)
a_slice = in_any_slice(5, goodIs)
assertEqual(a_slice, True)

w_slice = which_slice(6, goodIs)
assertEqual(w_slice, -1)
a_slice = in_any_slice(6, goodIs)
assertEqual(a_slice, False)


infile_path = None
infile_name = "YAMLObject_fromCodeConverter.py"

if not os.path.isfile(infile_name):
    for i in range(len(try_dirs)):
        try_dir = try_dirs[i]
        try_path = os.path.join(try_dir, infile_name)
        if os.path.isfile(try_path):
            infile_path = try_path
            if i != test_data_dir_i:
                print("WARNING: Using external data file \"{}\" makes"
                      " the test non-deterministic if it doesn't match"
                      " the one in \"{}\"."
                      "".format(infile_path, test_data_dir))
            break
else:
    infile_path = os.path.realpath(infile_name)

if infile_path is None:
    raise RuntimeError("\"{}\" was not in any known location {}"
                       "".format(infile_name, try_dirs))

outfile_path = os.path.join(testOutDir, "YAMLObject.py")
id_outfile_name = "pycodetool last run - identifiers.txt"
id_outfile_path = os.path.join(testOutDir, id_outfile_name)

parser = pct.PCTParser(infile_path)
print("* processing \"{}\"...".format(infile_path))
parser.framework_to_standard_python(outfile_path)
parser.save_identifier_lists(id_outfile_path)
print("* saved identifiers to \"{}\"".format(id_outfile_path))
print("* saved result to \"{}\"".format(outfile_path))
