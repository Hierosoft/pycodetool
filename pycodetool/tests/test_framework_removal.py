#!/usr/bin/env python3
import os
import platform
from unittest import TestCase

from pycodetool import (
    pct,
    echo0,
    set_verbosity,
)

profile = None
AppDatas = None

if platform.system() == "Windows":
    profile = os.environ.get("USERPROFILE")
    if profile is None:
        echo0("ERROR: You must set USERPROFILE in Windows.")
        exit(1)
    # AppDatas = os.path.join(profile, "AppData", "Roaming")
    AppDatas = os.environ['APPDATA']
else:
    profile = os.environ.get("HOME")
    if profile is None:
        echo0("ERROR: You must set HOME in a non-Windows platform.")
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

# test_data_dir = os.path.join("tests", "data")
test_data_dir = os.path.join("pycodetool", "tests", "data")
try_dirs.append(test_data_dir)
test_data_dir_i = len(try_dirs) - 1

try_dirs.append(ba)


class TestFrameworkRemoval(TestCase):

    def assertAllEqual(self, list1, list2, tbs=None):
        '''
        [copied from pycodetools.parsing by author]
        '''
        if len(list1) != len(list2):
            echo0("The lists are not the same length: list1={}"
                  " and list2={}".format(list1, list2))
            self.assertEqual(len(list1), len(list2))
        for i in range(len(list1)):
            try:
                self.assertEqual(list1[i], list2[i])
            except AssertionError as ex:
                if tbs is not None:
                    echo0("reason string (tbs): " + tbs)
                raise ex

    def test_framework_removal(self):
        echo0("* test framework to standard Python...")
        infile_path = None
        infile_name = "YAMLObject_fromCodeConverter.py"
        if not os.path.isfile(infile_name):
            for i in range(len(try_dirs)):
                try_dir = try_dirs[i]
                try_path = os.path.join(try_dir, infile_name)
                if os.path.isfile(try_path):
                    infile_path = try_path
                    if i != test_data_dir_i:
                        echo0("WARNING: Using external data file \"{}\" makes"
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
        echo0("  * processing \"{}\"...".format(infile_path))
        parser.framework_to_standard_python(outfile_path)
        parser.save_identifier_lists(id_outfile_path)
        echo0("  * saved identifiers to \"{}\"".format(id_outfile_path))
        echo0("  * saved result to \"{}\"".format(outfile_path))

