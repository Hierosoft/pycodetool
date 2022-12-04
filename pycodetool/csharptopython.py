# -*- coding: utf-8 -*-
import sys
import os
import pathlib

from pycodetool import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
)


# shares some code with io_csharptopython.io_csharp_to_python_file
def csharp_to_python_file(path, dest_dir):
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


def csharp_to_python(path, dest_dir, allow_make_dir=False,
                     use_hidden=False,
                     conv_fn=csharp_to_python_file):
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
        return conv_fn(path, dest_dir)
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
                conv_fn=conv_fn,
            )
            if code != 0:
                break
        return code
    echo0('Error: "{}" is neither a file nor directory.'.format(path))
    return 1
