#!/usr/bin/env python3
'''
# csharptopython
This module utilizes
[csharp-to-python](https://github.com/poikilos/csharp-to-python).

You must specify a file or directory followed by a destination
directory:

cs2python <source dir/file> <destination dir> [options]


OPTIONS:
--converter <path>       Set the converter{}.

'''
# csharp-to-python
import os
import sys
import shutil
import pathlib
import subprocess
from pycodetool import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
)

HOME = pathlib.Path.home()
DOWNLOADS = os.path.join(HOME, "Downloads")
# DEFAULT_CONVERTER = os.path.join(DOWNLOADS, "git", "shannoncruey",
#                                  "csharp-to-python", "convert.py")
DEFAULT_CONVERTER = os.path.join(HOME, "git",
                                 "csharp-to-python", "convert.py")
CONVERTER = DEFAULT_CONVERTER


def usage():
    echo0(__doc__.format(' such as "'+DEFAULT_CONVERTER+'"'))


def io_set_converter(path):
    '''
    Set the converter such as
    ~/git/csharp-to-python/convert.py.
    This function only works with other io_* functions, so the converter
    script must input a convert.in file in the same directory as the
    script, and output a convert.out file in the same directory as the
    script.
    '''
    global CONVERTER
    CONVERTER = path


def io_csharp_to_python_file(path, dest_dir):
    '''
    Convert a single C# file to a single py file using CONVERTER
    poikilos/csharp-to-python (or whatever converter script is
    set via the set_converter function).
    '''
    if not os.path.isfile(CONVERTER):
        raise ValueError('The converter script "{}" does not exist.'
                         ''.format(CONVERTER))
    if not os.path.isfile(path):
        raise ValueError('"{}" does not exist.'.format(dest_dir))
    if not os.path.isdir(dest_dir):
        raise ValueError('"{}" does not exist.'.format(dest_dir))

    path = os.path.abspath(path)
    dest_dir = os.path.abspath(dest_dir)
    # ^ Set abs paths to avoid issues with chdir below.
    nameNoExt, dotExt = os.path.splitext(os.path.split(path)[1])
    if not dotExt.lower() == ".cs":
        raise ValueError('"{}" is not a cs file.'.format(dotExt))
    else:
        echo1('nameNoExt="{}"'.format(nameNoExt))
    echo1('dest_dir="{}"'.format(dest_dir))
    dst_name = nameNoExt + ".py"
    dst_path = os.path.join(dest_dir, dst_name)
    echo1('# * converting "{}" to "{}"...'.format(path, dst_path))
    prev_dir = os.getcwd()

    repo_dir = os.path.dirname(CONVERTER)
    io_in = os.path.join(repo_dir, "convert.in")
    io_out = os.path.join(repo_dir, "convert.out")
    if os.path.isfile(io_in):
        os.remove(io_in)
    if os.path.isfile(io_out):
        os.remove(io_out)
    os.chdir(repo_dir)
    shutil.copy(path, io_in)
    cmd_parts = ["python2", CONVERTER]
    subprocess.check_output(cmd_parts)
    if not os.path.isfile(io_out):
        os.chdir(prev_dir)
        raise RuntimeError(
            '{} did not produce "{}"'.format(cmd_parts, io_out)
        )
    shutil.move(io_out, dst_path)
    '''
    if not os.path.isfile(dst_path):
        raise RuntimeError(
            'mv "{}" "{}" # failed.'.format(io_out, dst_path)
        )
    '''
    # echo0('  - generated "{}"'.format(dst_path))
    echo0('rm "{}"'.format(dst_path))
    echo0('rmdir "{}"'.format(os.path.dirname(dst_path)))
    os.chdir(prev_dir)
    return 0


def io_csharp_to_python(path, dest_dir, allow_make_dir=False,
                        use_hidden=False):
    '''
    Use poikilos/csharp-to-python to read input C# files and output
    py files then put the resulting convert.out file into the
    destination with the correct name (keep filename from path but
    change the extension).

    Keyword arguments:
    allow_make_dir -- Make dest_dir if it does not exist. This argument
        should usually be set to False, but it is set automatically to
        True during recursive calls.
    use_hidden -- Include hidden files.
    '''
    if not os.path.isdir(dest_dir):
        if allow_make_dir:
            os.makedirs(dest_dir)
        else:
            raise ValueError('"{}" does not exist.'.format(dest_dir))

    if os.path.isfile(path):
        return io_csharp_to_python_file(path, dest_dir)
    elif os.path.isdir(path):
        code = 0
        for sub in os.listdir(path):
            if sub.startswith("."):
                if not use_hidden:
                    continue
            subPath = os.path.join(path, sub)
            parent = os.path.join(dest_dir, sub)
            if os.path.isfile(subPath):
                parent = dest_dir
                if not sub.lower().endswith(".cs"):
                    echo0('# * skipping non-cs file "{}"'
                          ''.format(subPath))
                    continue
            code = io_csharp_to_python(
                subPath,
                parent,
                allow_make_dir=True,
            )
            if code != 0:
                break
        return code
    echo0('Error: "{}" is neither a file nor directory.'.format(path))
    return 1


def main():
    locations = []
    key = None
    options = {}
    for argI in range(1, len(sys.argv)):
        arg = sys.argv[argI]
        if key is not None:
            options[key] = arg
            key = None
        elif arg.startswith("-"):
            if arg == "--verbose":
                set_verbosity(1)
            elif arg == "--debug":
                set_verbosity(2)
            elif arg == "--converter":
                key = "converter"
            else:
                echo0("Error: {} is not a valid argument.".format(arg))
                return 1
        else:
            if len(locations) < 2:
                if os.path.isfile(arg):
                    locations.append(arg)
                elif os.path.isdir(arg):
                    locations.append(arg)
                else:
                    echo0('Error: "{}" is neither a file nor directory.'
                          ''.format(arg))
                    return 1
            else:
                echo0('Error: You must only specify a source,'
                      ' destination, and arguments,'
                      ' but you also specified "{}"'.format(arg))
                return 1
    if key is not None:
        echo0("Error: {} must be followed by a value.".format(key))
        return 1
    if len(locations) != 2:
        usage()
        echo0("Error: only got {}".format(locations))
        return 1

    return io_csharp_to_python(locations[0], locations[1])


if __name__ == "__main__":
    sys.exit(main())
