import pct
import os

base_dir = "C:\\Users\\Owner\\Documents\\GitHub\\blockability"
infile_path = "YAMLObject_fromCodeConverter.py"
if not os.path.isfile(infile_path):
    infile_path = os.path.join(base_dir,infile_path)
outfile_path = "YAMLObject.py"
if not os.path.isfile(outfile_path):
    outfile_path = os.path.join(base_dir,outfile_path)

parser = pct.PCTParser(infile_path)
parser.framework_to_standard_python(outfile_path)
