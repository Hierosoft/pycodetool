import pct
import os

try_dir = "C:\\Users\\Owner\\Documents\\GitHub\\blockability"
infile_path = "YAMLObject_fromCodeConverter.py"
outfile_path = "YAMLObject.py"
id_outfile_path = "last run - identifiers.txt"
if not os.path.isfile(infile_path):
    infile_path = os.path.join(try_dir,infile_path)
if os.path.isdir(try_dir):
    outfile_path = os.path.join(try_dir,outfile_path)
    id_outfile_path = os.path.join(try_dir,id_outfile_path)

parser = pct.PCTParser(infile_path)
parser.framework_to_standard_python(outfile_path)
parser.save_identifier_lists(id_outfile_path)
