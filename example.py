import pycodetool.pct as pct
import os
import platform

profile = None
if platform.system() == "Windows":
    profile = os.environ.get("USERPROFILE")
    if profile is None:
        print("ERROR: You must set USERPROFILE in Windows.")
        exit(1)
else:
    profile = os.environ.get("HOME")
    if profile is None:
        print("ERROR: You must set HOME in a non-Windows platform.")
        exit(1)

try_dir = os.path.join(profile, "Documents", "GitHub", "blockability")
infile_path = "YAMLObject_fromCodeConverter.py"
outfile_path = os.path.join(profile, "Documents", "YAMLObject.py")
id_outfile_name = "pycodetool last run - identifiers.txt"
id_outfile_path = os.path.join(profile, "Documents", id_outfile_name)
try_path = os.path.join(try_dir, infile_path)
if not os.path.isfile(infile_path):
    if os.path.isfile(try_path):
        infile_path = try_path
if os.path.isdir(try_dir):
    outfile_path = os.path.join(try_dir,outfile_path)
    id_outfile_path = os.path.join(try_dir,id_outfile_path)

parser = pct.PCTParser(infile_path)
print("* processing \"{}\"...".format(infile_path))
parser.framework_to_standard_python(outfile_path)
parser.save_identifier_lists(id_outfile_path)
print("* saved \"{}\"".format(id_outfile_path))
