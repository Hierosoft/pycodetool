# -*- coding: utf-8 -*-
"""
Parse data and manipulate variables.
"""
# Copyright (C) 2018-2022 Jake Gustafson

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

from __future__ import print_function
from __future__ import division
import os
import sys
import traceback
import copy
# import chardet  # not built-in
import codecs

from .find_hierosoft import hierosoft
# ^ also works for submodules since changes sys.path

from hierosoft.logging import (
    echo0,
    echo1,
    echo2,
    get_verbosity,
)

from pycodetool import (
    DATA_DIR,
)
from pycodetool.exactconfig import (
    ECLineInfo,
)
me = "pycodetool.parsing"

try:
    input = raw_input
except NameError:
    pass

# os_name is deprecated--use: import platform, then
# if "windows" in platform.system().lower(): do windows things

# formerly pcttext:
# uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# lowercase_chars = uppercase_chars.lower()
# letter_chars = uppercase_chars+lowercase_chars
digit_chars = "0123456789"
# identifier_chars = letter_chars+"_"+digit_chars
# identifier_and_dot_chars = identifier_chars + "."

# formerly from pgrs formerly poikilosregressionsuite:
alpha_upper_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alpha_lower_chars = alpha_upper_chars.lower()
alpha_chars = alpha_upper_chars+alpha_lower_chars
# numeric_chars = "1234567890"
alnum_chars = alpha_chars+digit_chars
identifier_chars = alnum_chars+"_"
identifier_and_dot_chars = identifier_chars+"."
entries_modified_count = 0
DEFAULT_CO = "UTF-8"
# DEFAULT_CO = "cp437"
# DEFAULT_DEC = "UTF-8"
# ^ Was able to display Prusa's German spelling in Marlin's Configuration_adv.h
#   but was not able to save correctly (meld read corrupt characters for that
#   and the Ohms symbol)
#   - To find the word Prusa in there if corrupt, look up "the official Pr"
DEFAULT_DEC = "UTF-8"


class AbstractFn:
    '''
    Properties
    name -- anything else before the open parenthesis, such as the
        function name etc. (The caller should clean up this part so it
        is only the function name before creating an AbstractFn). This
        should only be None if allow_bare_args and the data didn't
        contain an open parenthesis.
    raw_params -- a list where each element is a recieved function
        parameter stored as a string (using the syntax of the source
        language to appropriately represent the type).
    source_path -- the source code file that produced the function,
        otherwise None.
    line_n -- the source code line number that produced the function,
        starting at 1, otherwise None.
    '''
    def __init__(self, line, comment_delimiters=['#'],
                 allow_bare_args=False,
                 source_path=None, line_n=None):
        '''
        See "parse" documentation.
        '''
        self.parse(
            line,
            comment_delimiters=comment_delimiters,
            allow_bare_args=allow_bare_args,
            source_path=source_path,
            line_n=line_n,
        )

    def clear(self):
        self.raw_params = None
        self.raw_params_slices = None
        self.source_path = None
        self.line_n = None
        self.after = None
        self.raw_name = None

    def parse(self, line, comment_delimiters=['#'],
              allow_bare_args=False,
              source_path=None, line_n=None,
              allow_escaping_quotes=True):
        '''
        Keyword arguments:
        allow_bare_args -- Allow a line without the opening
            parenthesis (If False, raise ValueError if no
            [non-commented] "(").
        source_path -- The source code path that contains the function,
            (for debugging purposes, stored).
        line_n -- The source code line number, starting with 1,
            that contains the function (for debugging purposes, stored).
        '''
        self.clear()
        self.source_path = source_path
        self.line_n = line_n
        if comment_delimiters is None:
            comment_delimiters = []
        if isinstance(comment_delimiters, str):
            raise ValueError(
                "comment_delimiters should be a list-like object."
            )
        if line is None:
            return
        open_paren_i = find_unquoted_not_commented(
            line,
            "(",
            allow_escaping_quotes=allow_escaping_quotes,
        )
        start = 0
        close_paren_i = None
        if open_paren_i >= 0:
            start = open_paren_i + 1
            self.raw_name = line[:open_paren_i]
            if len(self.name) == 0:
                raise ValueError(
                    'There is no function name in `{}`'
                    ''.format(line)
                )
            close_paren_i = find_in_code(
                line,
                ")",
                start=start,
                # endbefore=endbefore,
                comment_delimiters=comment_delimiters,
                enclosures=["()"],
                allow_quoted=False,
                allow_escaping_quotes=allow_escaping_quotes,
            )
            # ^ find the end parenthesis accounting for nesting
            if close_paren_i <= open_paren_i:
                raise ValueError(
                    'There is no closing ")" in `{}`'
                    ''.format(line)
                )
        else:
            if not allow_bare_args:
                raise ValueError(
                    'allow_bare_args is False but there is no'
                    ' uncommented "(" in `{}`'
                    ''.format(line)
                )
        args_index = open_paren_i + 1
        args_part = line[args_index:close_paren_i]
        results = explode_unquoted(
            args_part,
            ",",
            get_str_i_tuple=True,
            strip=False,
            allow_escaping_quotes=allow_escaping_quotes,
        )
        self.raw_params = []
        self.raw_params_slices = []
        for t in results:
            param, p_start, p_end = t
            self.raw_params.append(param)
            self.raw_params_slices.append(
                (p_start+args_index, p_end+args_index)
            )
        self.after = line[close_paren_i+1:]

    @property
    def name(self):
        return self.raw_name.strip()

    @name.setter
    def name(self, name):
        prev_raw_name = self.raw_name
        self.raw_name = name
        self.name = name.strip()
        # if prev_raw_name is not None:
        #     delta = len(self.raw_name) - len(prev_raw_name)

    def line_error(self, error):
        result = ""
        if self.source_path is not None:
            result = self.source_path + ":"
            if (self.line_n is not None) and (self.line_n >= 1):
                result += str(self.line_n) + ": "
            else:
                result += " "
        return result + error

    def set_param(self, index, code):
        '''
        Sequential arguments:
        code -- the code, including quotes if any, which defines the
            value (Examples: `"Hello"`, `True`, 100)
        '''
        self.raw_params[index] = code

    def to_string(self):
        result = ""
        if self.raw_name is not None:
            result += self.raw_name
        if self.raw_name.strip().endswith("("):
            raise ValueError(
                'The function name "{}" must not end with "("'
                ''.format(self.raw_name)
            )
        result += "("
        sep = ""
        for raw_param in self.raw_params:
            result += sep
            result += raw_param
            sep = ","
        result += ")"
        return result


class InstalledFile:
    source_dir_path = None
    dest_dir_path = None
    file_name = None

    def __init__(self, file_name, source_dir_path, dest_dir_path):
        self.file_name = file_name
        self.source_dir_path = source_dir_path
        self.dest_dir_path = dest_dir_path


class ConfigManager:
    """
    For ExactConfig (maintaining comments, checking comments to put
    values near comments for them) see exactconfig in
    github.com/poikilos/pycodetool
    """
    # config_name = None
    _config_path = None
    _data = None
    _ao = None

    def __init__(self, config_file_path, assignment_operator_string):
        """DOES load variables if path exists"""
        self._data = {}
        self._config_path = config_file_path
        self._ao = assignment_operator_string
        self._data = get_dict_modified_by_conf_file(
            self._data,
            self._config_path, self._ao
        )

    def load_var(self, name, default_value, description,
                 interactive_enable=False):
        """
        Keyword arguments:
        interactive_enable -- If true, this method DOES ask for user
            input if a variable does not exist. If default_value is
            None, do not add the variable to _data if not entered.
        """
        is_changed = False
        if name not in self._data:
            echo2("")
            if default_value is None:
                echo0("WARNING: this program does not have a"
                      + " default value for "+name+".")
                default_value = ""
            if interactive_enable:
                answer = input("Please enter " + description + " ("
                               + name + ") [blank for " + default_value
                               + "]: ")
            else:
                answer = default_value
            if answer is not None:
                answer = answer.strip()

            if answer is not None and len(answer) > 0:
                self._data[name] = answer
            else:
                self._data[name] = default_value
            echo1("Using " + name + " '" + self._data[name] + "'")
            is_changed = True

        if not os.path.isfile(self._config_path):
            is_changed = True
            echo1("Creating '"+self._config_path+"'")
        if is_changed:
            self.save_yaml()

    def prepare_var(self, name, default_value, description,
                    interactive_enable=True):
        self.load_var(
            name,
            default_value,
            description,
            interactive_enable=interactive_enable
        )

    def contains(self, name):
        return (name in self._data.keys())

    def remove_var(self, name):
        try:
            del self._data[name]
            self.save_yaml()
        except KeyError:
            pass

    def set_var(self, name, val):
        """DOES autosave IF different val"""
        is_changed = False
        if name not in self._data.keys():
            echo0("[ ConfigManager ] WARNING to developer: run"
                  " prepare_var before set_val, so that variable has a"
                  " default.")
            is_changed = True
        elif self._data[name] != val:
            is_changed = True
        if is_changed:
            self._data[name] = val
            self.save_yaml()

    def keys(self):
        return self._data.keys()

    def get_var(self, name):
        result = None
        if name in self._data:
            result = self._data[name]
        return result

    def save_yaml(self):
        save_conf_from_dict(self._config_path, self._data, self._ao,
                            save_nulls_enable=False)


class SourceFileInfo:
    def __init__(self, repo_path, relative_path, encoding=None):
        self.repo_path = repo_path
        self.relative_path = relative_path
        self._unsaved_lines = []
        self._lines, self._encoding = try_readlines(
            self.full_path(),
            encoding=encoding,
        )
        self._unsaved_d = {}

    def full_path(self):
        return os.path.join(self.repo_path, self.relative_path)

    def save_changes(self):
        '''
        Save the file only if there are lines changed by the
        set_ or insert_ methods.
        '''
        count = len(self._unsaved_lines)
        if count < 1:
            return count
        path = self.full_path()
        write_lines(path, self._lines, encoding=self._encoding)
        self._unsaved_lines.clear()
        self._unsaved_d.clear()
        return count

    def get_cached(self, name, line_index=None):
        '''
        Get the value whether it is saved or in cache. Also get other
        info as part of a tuple as described under "Returns" in the
        get_cdef documentation.

        Keyword arguments:
        line_index -- If this is set, use this line index (starting at
            0) and ignore the name.
        '''
        if name in self._unsaved_d.keys():
            # ^ Don't depend on .get since None is ok to return to
            #   check for the presence of the setting.
            return self._unsaved_d[name], -1, name, None
        results = get_cdef(
            self.full_path(),
            name,
            lines=self._lines,
            line_index=line_index,
        )
        # skip=skip
        return results

    def set_cached(self, name, value, comments=None):
        '''
        Change C-like lines in the cache.
        For documentation see set_cdef(None, ..., lines=...).

        Returns:
        a tuple containing a list of lines that changed and a list of
        ECLineInfo objects representing values not changed.
        '''
        changes, unaffected_items = set_cdef(
            self.relative_path,  # OK since using lines; necessary for tracking
            name,
            value,
            comments=comments,
            lines=self._lines,
            encoding=self._encoding,
        )
        self._unsaved_d.update(cdefs_to_d(self.full_path(), changes))
        self._unsaved_lines += changes
        return changes, unaffected_items

    def insert_cached(self, new_lines, after=None, before=None):
        '''
        Insert C-like lines into the cache.
        For documentation see insert_lines(None, ..., lines=...).

        Returns:
        True if success, False if failed.
        '''
        self._unsaved_lines += new_lines
        # Cache the values in case there are values in new_lines
        #   (stored in self._unsaved_d later *only* if actually
        #   inserted).
        after_d = cdefs_to_d(self.full_path(), lines=new_lines)
        # before_d = cdefs_to_d(self.full_path(), lines=self.lines)
        if insert_lines(None, new_lines, after=after, before=before,
                        lines=self._lines,
                        encoding=self._encoding):
            self._unsaved_d.update(after_d)
            return True
        return False


warned_suffixes = []


def isnumber(s, suffixes=None):
    '''
    Unlike s.isdigit(), s.isdecimal() or even s.isnumeric(), only ensure
    an int-like or float-like number:
    - use float casting
    - allow "." and "-" if appropriate (if float casting works)

    This is the same as RepresentsFloat for the time being.

    Keyword arguments:
    suffixes -- Remove (only up to the first found of) these suffixes
        before testing.
    '''
    if suffixes is not None:
        if ((not isinstance(suffixes, list))
                and (not isinstance(suffixes, tuple))):
            raise ValueError("suffixes must be a list or tuple.")
        for suffix in suffixes:
            if len(suffix) > 1:
                if suffix not in warned_suffixes:
                    echo0('Warning: suffix "{}" was not expected'
                          ' to have more than one character.'
                          ''.format(suffix))
                    warned_suffixes.append(suffix)
            elif len(suffix.strip()) == 0:
                raise ValueError("A suffix is blank.")
            elif len(suffix.strip()) != len(suffix):
                raise ValueError("A suffix mustn't contain spacing.")
            if s.endswith(suffix):
                s = s[:-len(suffix)]
                break
    try:
        f = float(s)
    except ValueError:
        return False
    return True


def slice_is_space(s, start, end):
    '''
    Unlike s.[start:end].isspace(), ensure there is actually the
    expected number of spacing characters there rather than being out
    of range.
    '''
    if start is None:
        start = 0
    if end is None:
        end = len(s)
    # Getting the length only works with positive numbers due to
    # negative slice indices not being on a number line where they are
    # in math, so calculate start_pos and end_pos:
    start_pos = start
    if start_pos < 0:
        start_pos = len(s) + start
    end_pos = end
    if end_pos < 0:
        end_pos = len(s) + end
    expected_len = end_pos - start_pos
    if len(s[start:end]) != expected_len:
        if get_verbosity() > 1:
            echo2('The slice "{}" ("{}"[{}:{}]) is out of range.'
                  ' There is not enough space.'
                  ''.format(s[start:end], s, start, end))
        return False
    if get_verbosity() > 1:
        if not s[start:end].isspace():
            echo2('The slice is not space: "{}"'
                  ''.format(s[start:end].isspace()))

    return s[start:end].isspace()


def toPythonLiteral(v):
    '''
    [copied to nopackage by author]
    '''
    # a.k.a. to_python_literal a.k.a. unparse_python_literal
    if v is None:
        return None
    elif v is False:
        return "False"
    elif v is True:
        return "True"
    elif ((type(v) == int) or (type(v) == float)):
        return str(v)
    elif (type(v) == tuple) or (type(v) == list):
        enclosures = '()'
        if type(v) == list:
            enclosures = '[]'
        s = enclosures[0]
        for val in v:
            s += toPythonLiteral(val) + ", "
            # ^ Ending with an extra comma has no effect on length.
        s += enclosures[1]
        return s
    return "'{}'".format(
        v.replace("'", "\\'").replace("\r", "\\r").replace("\n", "\\n")
    )


def assertEqual(v1, v2, tbs=None):
    '''
    Show the values if they differ before the assertion error stops the
    program. If your test case inherits unittest.TestCase,
    use the self.assertEqual from super instead of this unless you want
    the errors in a format this function provides.

    Unit tests in this module use this special assertEqual since it
    accepts an extra argument below.

    Keyword arguments:
    tbs -- traceback string (either caller or some sort of message to
        show to describe what data produced the arguments if they're
        derived from something else)
    '''
    if ((v1 is True) or (v2 is True) or (v1 is False) or (v2 is False)
            or (v1 is None) or (v2 is None)):
        if v1 is not v2:
            echo0("")
            echo0("{} is not {}".format(toPythonLiteral(v1),
                                        toPythonLiteral(v2)))
            if tbs is not None:
                echo0("for {}".format(tbs))
        assert v1 is v2
    else:
        if v1 != v2:
            echo0("")
            echo0("{} != {}".format(toPythonLiteral(v1),
                                    toPythonLiteral(v2)))
            if tbs is not None:
                echo0("while {}".format(tbs))
        assert v1 == v2


def assertAllEqual(list1, list2, tbs=None):
    '''
    Assert that each element matches. If your test case inherits
    unittest.TestCase, don't use this. Instead, write your own
    assertAllEqual similar to this in your class but call
    self.assertEqual instead of assertEqual.
    '''
    if len(list1) != len(list2):
        echo0("The lists are not the same length: list1={}"
              " and list2={}".format(list1, list2))
        assertEqual(len(list1), len(list2))
    for i in range(len(list1)):
        assertEqual(list1[i], list2[i], tbs=tbs)


def get_dict_deepcopy(old_dict):
    new_dict = None
    if type(old_dict) is dict:
        new_dict = {}
        for this_key in old_dict:
            new_dict[this_key] = copy.deepcopy(old_dict[this_key])
    elif old_dict is None:
        return None
    return new_dict


def ts_equals(v1, v2, tb=None):
    '''
    Type-sensitive equals: uses the proper comparison operator depending
    on the type.

    Keyword arguments:
    tb -- traceback (any string that should show along with an error or
          warning). If None, do not show warnings (warnings are when:
          type differs).
    '''
    if type(v1) != type(v2):
        if tb is not None:
            if (v1 is not None) and (v2 is not None):
                echo0("[ {} ts_equals ] WARNING: Types differ for {}."
                      " v1 is {} and v2 is {}"
                      "".format(me, tb, type(v1).__name__,
                                type(v2).__name__))
        return False
    if type(v1).__name__ == "bool":
        return v1 is v2
    return v1 == v2


def is_dict_subset(new_dict, old_dict,
                   verbose_dest_description="unknown file"):
    '''
    Is anything in new_dict not in (or different from) old_dict.
    '''
    tb = verbose_dest_description
    is_changed = False
    if old_dict is None:
        if new_dict is not None:
            is_changed = True
        return is_changed
    if new_dict is None:
        # There is no new information, so that counts as not changed.
        return False
    old_dict_keys = old_dict.keys()
    for this_key in new_dict:
        if (this_key not in old_dict_keys):
            is_changed = True
            echo1("SAVING '" + verbose_dest_description
                  + "' since " + str(this_key)
                  + " not in saved version.")
            break
        elif not ts_equals(new_dict[this_key], old_dict[this_key],
                           tb=this_key+" in is_dict_subset for "+tb):
            echo1("SAVING '" + verbose_dest_description
                  + "' since " + str(this_key)
                  + " not same as saved version.")
            break
    return is_changed


def vec2_not_in(this_vec, this_list):
    result = False
    if this_list is not None and this_vec is not None:
        for tryV in this_list:
            if (tryV[0] == this_vec[0]) and (tryV[1] == this_vec[1]):
                result = True
                break
    return result


def ivec2_equals(pos1, pos2):
    return ((int(pos1[0]) == int(pos2[0])) and
            (int(pos1[1]) == int(pos2[1])))


def get_dict_from_conf_file(path, assignment_operator="=",
                            comment_delimiter="#",
                            inline_comments_enable=False):
    results = None
    results = get_dict_modified_by_conf_file(
        results,
        path,
        assignment_operator,
        comment_delimiter=comment_delimiter,
        inline_comments_enable=inline_comments_enable
    )
    return results


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def RepresentsFloat(s):
    '''
    This is the same as isnumber for now.
    '''
    try:
        float(s)
        return True
    except ValueError:
        return False


def view_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    print(indent+str(ex_type))
    print(indent+str(ex))
    traceback.print_tb(tb)
    del tb


def print_file(path, indent=""):
    line_count = 0
    if path is None:
        echo0(indent+"print_file: path is None")
        return 0
    if not os.path.isfile(path):
        echo0(indent+"print_file: file does not exist")
        return 0
    try:
        if indent is None:
            indent = ""
        ins = open(path, 'r')
        rawl = True
        while rawl:
            rawl = ins.readline()
            line_count += 1
            if rawl:
                print(indent+rawl)
        ins.close()
        # if line_count == 0:
        #     print(indent + "print_file WARNING: "
        #           + str(line_count)+" line(s) in '"+path+"'")
        # else:
        #     print(indent + "# " + str(line_count)
        #           + " line(s) in '" + path + "'")
    except PermissionError as ex:
        echo0(indent+'print_file: could not read "{}": {}'
              "".format(path, ex))
    return line_count


def singular_or_plural(singular, plural, count):
    result = plural

    if count == 1:
        result = singular
    return str(count) + " " + result


def get_entries_modified_count():
    return entries_modified_count


def get_dict_modified_by_conf_file(this_dict, path,
                                   assignment_operator="=",
                                   comment_delimiter="#",
                                   inline_comments_enable=False):
    global entries_modified_count
    nulls = ["None", "null", "~", "NULL"]
    entries_modified_count = 0
    results = this_dict
    # echo2("Checking "+str(path)+" for settings...")
    if (results is None) or (type(results) is not dict):
        results = {}
    if os.path.isfile(path):
        echo1("[ ConfigManager ] Using existing '" + path + "'")
        ins = open(path, 'r')
        rawl = True
        line_n = 0
        while rawl:
            line_n += 1  # This must become 1 on the first line.
            rawl = ins.readline()
            if not rawl:
                break
            strp = rawl.strip()
            if len(strp) < 1:
                continue
            if strp[0:len(comment_delimiter)] == comment_delimiter:
                continue
            if strp[0] == "-":
                # ignore yaml arrays
                continue
            if inline_comments_enable:
                comment_index = strp.find(comment_delimiter)
            ao_index = strp.find(assignment_operator)
            if ao_index < 1:
                # < 1 instead of < 0 to skip 0-length variable names
                continue
            if ao_index >= len(strp) - 1:
                continue
            # skip yaml implicit nulls or
            # yaml objects
            result_name = strp[:ao_index].strip()
            result_val = strp[ao_index+1:].strip()
            result_lower = result_val.lower()
            if result_val in nulls:
                result_val = None
            elif result_lower == "true":
                result_val = True
            elif result_lower == "false":
                result_val = False
            elif RepresentsInt(result_val):
                result_val = int(result_val)
            elif RepresentsFloat(result_val):
                result_val = float(result_val)
            # echo2("   CHECKING... " + result_name
            #       + ":"+result_val)
            if ((result_name not in results) or
                    (results[result_name] != result_val)):
                entries_modified_count += 1
                # echo2(str(entries_modified_count))
            results[result_name] = result_val
        ins.close()
    return results


def save_conf_from_dict(path, this_dict, assignment_operator="=",
                        save_nulls_enable=True):
    try:
        outs = open(path, 'w')
        for this_key in this_dict.keys():
            if save_nulls_enable or (this_dict[this_key] is not None):
                if this_dict[this_key] is None:
                    outs.write(this_key + assignment_operator
                               + "null\n")
                else:
                    outs.write(this_key + assignment_operator
                               + str(this_dict[this_key]) + "\n")
        outs.close()
    except PermissionError as e:
        echo0("Could not finish saving chunk metadata to '" + str(path)
              + "': " + str(traceback.format_exc()))
        echo0(e)


def get_list_from_hex(hex_string):
    results = None
    if hex_string is not None:
        if len(hex_string) >= 2:
            if hex_string[:2] == "0x":
                hex_string = hex_string[2:]
            elif hex_string[:1] == "#":
                hex_string = hex_string[1:]
            if len(hex_string) > 0 and \
                    hex_string[len(hex_string)-1:] == "h":
                hex_string = hex_string[:len(hex_string)-1]
            index = 0
            while index < len(hex_string):
                if results is None:
                    results = list()
                if len(hex_string)-index >= 2:
                    results.append(int(hex_string[index:index+2], 16))
                index += 2

    return results


def s_to_tuple(line, debug_src_name="<unknown object>"):
    """
    Convert a tuple-like string to a tuple of floats (or ints if fails).
    """
    # formerly get_tuple_from_notation
    result = None
    if line is not None:
        # mark chunk
        tuple_noparen_pos_string = line.strip("() \n\r")
        pos_strings = tuple_noparen_pos_string.split(",")
        if len(pos_strings) == 3:
            try:
                player_x = float(pos_strings[0])
                player_y = float(pos_strings[1])
                player_z = float(pos_strings[2])
            except ValueError:
                player_x = int(pos_strings[0])
                player_y = int(pos_strings[1])
                player_z = int(pos_strings[2])
            result = player_x, player_y, player_z
        else:
            echo0("'" + debug_src_name + "' has bad position data--"
                  + "should be 3-length (x,y,z) in position value: "
                  + str(pos_strings))
    return result


def is_same_fvec3(list_a, list_b):
    result = False
    if list_a is not None and list_b is not None:
        if len(list_a) >= 3 and len(list_b) >= 3:
            result = (float(list_a[0]) == float(list_b[0])) and \
                     (float(list_a[1]) == float(list_b[1])) and \
                     (float(list_a[2]) == float(list_b[2]))
    return False


def lastchar(val):
    result = None
    if (val is not None) and (len(val) > 0):
        result = val[len(val)-1]
    return result


def get_indent_string(line):
    ender_index = find_any_not(line, " \t")
    result = ""
    if ender_index > -1:
        result = line[:ender_index]
    return result


def is_identifier_valid(val, is_dot_allowed):
    result = False
    these_id_chars = identifier_chars
    if is_dot_allowed:
        these_id_chars = identifier_and_dot_chars
    for index in range(0, len(val)):
        if val[index] in these_id_chars:
            result = True
        else:
            result = False
            break
    return result


def find_slice(haystack, starter, ender):
    '''
    Find a pair of strings and get the slice to get or remove the string
    (index of starter, and index of ender + 1) or return -1, -1. The
    starter and ender can be the same character, and it must occur
    twice to count. Otherwise, ender must occur after starter to count.
    - If looking for multiple enclosures at once, use another function
      such as get_operation_chunk_len instead.
    - To get multiple slices, use another function such as
      explode_unquoted or quoted_slices instead.

    Sequential arguments:
    haystack -- The string to slice.
    starter -- The first needle such as "(".
    ender -- The second needle such as ")".
    '''
    startI = haystack.find(starter)
    if startI < 0:
        return -1, -1
    endI = haystack.find(ender, startI + 1)
    if endI < 0:
        return -1, -1
    return startI, endI+1


# formerly get_params_len
def get_operation_chunk_len(val, start=0, step=1, line_n=None):
    result = 0
    openers = "([{"
    closers = ")]}"
    quotes = "'\""
    ender = len(val)
    direction_msg = "after opening"
    if step not in [-1, 1]:
        raise ValueError("step must be -1 or 1 not {}.".format(step))

    if step < 0:
        tmp = openers
        openers = closers
        closers = tmp
        ender = -1
        direction_msg = "before closing"
    opens = ""
    closes = ""
    index = start
    in_quote = None
    line_message = ""
    if ((line_n is not None) and (line_n > -1)):
        line_message = "line "+str(line_n)+": "
    while (step > 0 and index < ender) or (step < 0 and index > ender):
        opener_number = openers.find(val[index])
        closer_number = closers.find(val[index])
        expected_closer = None
        if (len(closes) > 0):
            expected_closer = lastchar(closes)
        quote_number = quotes.find(val[index])
        if (in_quote is None) and (opener_number > -1):
            opens += openers[opener_number]
            closes += closers[opener_number]
        elif (in_quote is None) and (closer_number > -1):
            if closers[closer_number] == expected_closer:
                opens = opens[:len(opens)-1]
                closes = closes[:len(closes)-1]
        elif quote_number > -1:
            if in_quote is None:
                in_quote = val[index]
            else:
                if in_quote == val[index]:
                    if (index-1 == -1) or (val[index-1] != "\\"):
                        in_quote = None
        index += step
        result += 1
        if ((in_quote is None) and
                (len(opens) == 0) and
                ((index >= len(val)) or
                 (val[index] not in identifier_and_dot_chars))):
            break
    return result


def find_identifier(line, identifier_string, start=0):
    result = -1
    start_index = start
    lenid = 0
    if identifier_string is None:
        return -1
    lenid = len(identifier_string)
    if lenid < 1:
        return -1
    if line is None:
        return -1
    lenl = len(line)
    if lenl < 1:
        return -1
    while True:
        try_index = find_unquoted_not_commented(line,
                                                identifier_string,
                                                start=start_index)
        if try_index < 0:
            break
        # id_start = False
        # if try_index == 0:
        #     id_start = True
        # elif line[try_index-1] not in identifier_chars:
        # is_id = line[try_index-1] in identifier_chars
        can_start = False
        if try_index == 0:
            can_start = True
        elif line[try_index-1] not in identifier_chars:
            can_start = True
        is_alone = False

        if try_index + lenid == lenl:
            is_alone = True
        elif line[try_index+lenid] not in identifier_chars:
            is_alone = True

        if can_start and is_alone:
            result = try_index
            # input(identifier_string + "starts after '"
            #       + line[try_index] + "' ends before '"
            #       + line[try_index+lenid]
            #       + "'")
            break
        else:
            # match is part of a different identifier, so skip it
            # input(identifier_string + " does not after '"
            #       + line[try_index] + "' ends before '"
            #       + line[try_index+lenid]
            #       + "'")
            start_index = try_index + lenid
    return result


def get_newline_in_data(data):
    newline = None
    cr = "\r"
    lf = "\n"
    cr_index = -1
    lf_index = -1
    cr_index = data.find(cr)
    lf_index = data.find(lf)
    if (cr_index > -1) and (lf_index > -1):
        if cr_index < lf_index:
            newline = cr+lf
        else:
            newline = lf+cr
    elif cr_index > -1:
        newline = cr
    elif lf_index > -1:
        newline = lf
    return newline


def re_escape_visible(val):
    result = val.replace("\n", "\\n").replace("\n", "\\n")
    return result


def get_newline(file_path):
    data = None
    with open(file_path, "r") as myfile:
        data = myfile.read()
    return get_newline_in_data(data)


def is_allowed_in_variable_name_char(one_char):
    result = False
    if len(one_char) == 1:
        if one_char in identifier_chars:
            result = True
    else:
        echo0("error in is_allowed_in_variable_name_char: one_char"
              " must be 1 character")
    return result


def find_any_not(haystack, char_needles, start=None, step=1):
    result = -1
    if step not in [-1, 1]:
        raise ValueError("step must be -1 or 1 not {}.".format(step))

    if (len(char_needles) > 0) and (len(haystack) > 0):
        endbefore = len(haystack)
        if start is None:
            if step > 0:
                start = 0
            elif step < 0:
                start = len(haystack)-1
        if step < 0:
            endbefore = -1
        index = start

        while ((step > 0 and index < endbefore) or
                (step < 0 and index > endbefore)):
            if not haystack[index:index+1] in char_needles:
                result = index
                break
            index += step
    return result


def explode_unquoted(haystack, delimiter, get_str_i_tuple=False,
                     strip=True, quote_marks=['"', "'"],
                     allow_commented=False, min_indent="",
                     allow_escaping_quotes=True):
    '''
    Explode using a delimiter except quoted delimiters using double or
    single quotes. See quoted_slices for a function that uses quotes
    but not delimiters.

    Keyword arguments:
    get_str_i_tuple -- Get a list of tuples of (string, start, end)
        instead of a list of strings. The slice defined by start, end
        will include whitespace whether or not strip is used, though
        strip will affect the string.
    strip -- Remove whitespace from each element.
    min_indent -- The starting indent only used for logging.
    '''
    elements = list()
    start = 0
    echo2(min_indent+"explode_unquoted:")
    while True:
        if allow_commented:
            index = find_unquoted_even_commented(
                haystack,
                delimiter,
                start=start,
                 quote_marks=quote_marks,
                 min_indent=min_indent+"  ",
                 allow_escaping_quotes=allow_escaping_quotes,
            )
        else:
            index = find_unquoted_not_commented(
                haystack,
                delimiter,
                start=start,
                quote_marks=quote_marks,
                min_indent=min_indent+"  ",
                allow_escaping_quotes=allow_escaping_quotes,
            )
        echo2(min_indent+'- haystack[{}:]="{}"'
              ''.format(start, haystack[start:]))
        echo2(min_indent+'- index={}'
              ''.format(index))

        if index >= 0:
            hs = haystack
            element = hs[start:index].strip() if strip else hs[start:index]
            if get_str_i_tuple:
                elements.append((element, start, index))
            else:
                elements.append(element)
            start = index + 1  # +1 to skip the delimiter
            if start + len(elements[-1]) >= len(haystack):
                break
        else:
            echo2(min_indent+"END explode_unquoted due to {} not found"
                  "".format(delimiter))
            break

    element = haystack[start:].strip() if strip else haystack[start:]
    if allow_commented or (not element.startswith("#")):
        if get_str_i_tuple:
            elements.append((element, start, len(haystack)))
        else:
            elements.append(element)
    # ^ The rest of haystack is the param after
    #   last comma, else beginning if no comma
    #   (There is always at least 1 entry, the last entry).
    return elements


def find_dup(this_list, discard_whitespace_ignore_None_enable=True,
             ignore_list=None, ignore_numbers_enable=False):
    """
    DISCARD whitespace, and never match None to None
    """
    result = -1
    if type(this_list) is list:
        for i1 in range(0, len(this_list)):
            for i2 in range(0, len(this_list)):
                i1_strip = None
                i2_strip = None
                if this_list[i1] is not None:
                    i1_strip = this_list[i1].strip()
                if this_list[i2] is not None:
                    i2_strip = this_list[i2].strip()
                if (i1_strip is not None and
                        len(i1_strip) > 0 and
                        i2_strip is not None and
                        len(i2_strip) > 0):
                    if ((i1 != i2) and
                            (ignore_list is None or
                             i1_strip not in ignore_list) and
                            i1_strip == i2_strip):
                        number1 = None
                        # number2 = None
                        if ignore_numbers_enable:
                            try:
                                number1 = int(i1_strip)
                            except ValueError:
                                try:
                                    number1 = float(i1_strip)
                                except ValueError:
                                    pass
                            # only need one since they already are known
                            #   to match as text
                            # try:
                            #     number2 = int(i2_strip)
                            # except:
                            #     try:
                            #         number2 = float(i2_strip)
                            #     except:
                            #         pass
                        ignore_this = False
                        if ignore_numbers_enable:
                            ignore_this = number1 is not None
                        if not ignore_this:
                            result = i2
                            echo1("[" + str(i1) + "]:"
                                  + str(this_list[i1])
                                  + " matches [" + str(i2) + "]:"
                                  + str(this_list[i2]))
                            break
            if result > -1:
                break
    else:
        echo0("[ parsing.py ] ERROR in has_dups: " + str(this_list)
              + " is not a list")
    return result


def has_dups(this_list):
    return find_dup(this_list) > -1


def get_initial_value_from_conf(path, name, assignment_operator="="):
    """
    Get the first instance of name, get its value, then stop reading
    the file indicated by path.
    """
    result = None
    line_count = 0
    if path is not None:
        if os.path.isfile(path):
            ins = open(path, 'r')
            rawl = True
            while rawl:
                rawl = ins.readline()
                line_count += 1
                if rawl:
                    ao_i = rawl.find(assignment_operator)
                    if ao_i > 0:  # intentionall skip when 0
                        this_name = rawl[:ao_i].strip()
                        if this_name == name:
                            result = rawl[ao_i+1:].strip()
                            # NOTE: blank is allowed
                            break
            ins.close()
        else:
            echo0("ERROR in get_initial_value_from_conf: '" + str(path)
                  + "' is not a file.")
    else:
        echo0("ERROR in get_initial_value_from_conf: path is None.")
    return result


def find_which_needle(haystack, haystack_i, needles, subscript=None):
    '''
    Get the index in needles that exists at haystack[haystack_i:] or
    -1 if no needles are there.

    Keyword arguments:
    subscript -- if each needle is subscriptable, subscript it with
        subscript before using it. Otherwise (if None) each element of
        needle will be used directly as usual. Example: if needles is
        ["()", "{}"] then set subscript=0 to look for only "(" and "{".
    '''
    for i in range(len(needles)):
        needle = needles[i]
        if subscript is not None:
            needle = needles[i][subscript]
        if haystack[haystack_i:haystack_i+len(needle)] == needle:
            return i
    return -1


quoted_slices_error = None


def get_quoted_slices_error():
    return quoted_slices_error


def which_slice(v, ranges, length=None):
    '''
    Get the index of the slice (ranged pair) that contains v.

    Sequential arguments:
    v -- Check for this index within each range
    ranges -- A list of number pairs such as tuples [(start, stop),...]
        where start is inclusive and stop is exclusive as per Python
        slice and range notation.

    Keyword arguments:
    length -- If either of the values in any range is negative, you must
        provide the length of the string to which the slices refer (so
        that the real index can be calculated). Otherwise this function
        will raise a ValueError.

    Returns:
    The first index in ranges that has the range that contains v, or
    -1 if v was not in any ranges.
    '''
    for range_i in range(len(ranges)):
        r = ranges[range_i]
        start = r[0]
        stop = r[1]
        if start < 0:
            if length is not None:
                start = length + start
            else:
                raise ValueError("negative slice notation isn't"
                                 " implemented but a start index is"
                                 " negative in {}".format(ranges))
        if stop < 0:
            if length is not None:
                stop = length + stop
            else:
                raise ValueError("negative slice notation isn't"
                                 " implemented but a stop index is"
                                 " negative in {}".format(ranges))
        if (v >= r[0]) and (v < r[1]):
            return range_i
    return -1


def in_any_slice(i, ranges):
    return which_slice(i, ranges) > -1


END_BEFORE_QUOTE_ERR = "string ended before quote ended"


def quoted_slices(haystack, start=0, endbefore=None,
                  comment_delimiters=["#"]):
    '''
    Get a list of tuples where each tuple is the start and stop values
    for quoted portions of haystack. The first entry of the tuple is
    the first quotation mark (`"` or `'`) and the second entry of
    the tuple is 1 after the ending quote's index (as per slice
    notation). See explode_unquoted for a function that does something
    similar but also uses field delimiters (with get_str_i_tuple option
    to get slice start index).
    - For a hard slice search excluding comments use find_slice instead.

    Keyword arguments:
    comment_delimiters -- Use this to specify one or more comment
        delimiters. Examples: ['#'] for Python or ['#', '//'] for PHP
    '''
    if comment_delimiters is None:
        echo0("WARNING: quoted_slices got no comment delimiters.")
        comment_delimiters = []
    global quoted_slices_error
    quoted_slices_error = None
    results = []
    open_i = None
    i = start
    quotes = "\"'"
    if haystack is None:
        raise ValueError("haystack is None")
    if endbefore is None:
        endbefore = len(haystack)
    elif endbefore < 0:
        new_endbefore = len(haystack) + endbefore
        # ^ + since already negative
        echo2("INFO: endbefore was negative so it will"
              " change to len(haystack)+offset (endbefore={},"
              " new_endbefore={})."
              "".format(endbefore, new_endbefore))
        endbefore = new_endbefore
    if endbefore < start:
        raise ValueError("endbefore is < start which should never be"
                         " the case (endbefore={})"
                         "".format(endbefore))
    i -= 1
    open_i = None
    prev_c = None
    comment_started = False
    echo2("comment_delimiters={}".format(comment_delimiters))
    while i+1 < endbefore:
        i += 1
        c = haystack[i]
        echo2("( i={}, open_i={}, c={} )".format(i, open_i, c))
        if open_i is None:
            if c in quotes:
                open_i = i
            else:
                for c_delim in comment_delimiters:
                    if (haystack[i:i+len(c_delim)] == c_delim):
                        comment_started = True
                        break
                if comment_started:
                    break
        elif (c == haystack[open_i]) and (prev_c != "\\"):
            results.append((open_i, i+1))
            # ^ first quote & 1 after end quote as per slice notation
            #   (including both quotes)
            open_i = None
        prev_c = c
    if open_i is not None:
        quoted_slices_error = END_BEFORE_QUOTE_ERR
        echo0("WARNING: The quote ([{}]) wasn't closed in"
              " (i={}, endbefore={}):"
              "".format(open_i+1, i, endbefore))
        echo0("`{}`".format(haystack))
        end_mark_i = endbefore - (open_i+1)
        end_mark = ""
        if end_mark_i >= 0:
            # end_mark = "^end"
            pass
        echo0(" "*(open_i+1) + "^" + " "*end_mark_i + end_mark)
        # raise SyntaxError("END_BEFORE_QUOTE_ERR")

    return results


def find_in_code(haystack, needle, start=0, endbefore=None,
                 step=1, comment_delimiters=["#"],
                 enclosures=None, allow_quoted=True,
                 allow_commented=False, quote_marks=['"', "'"],
                 min_indent="", allow_escaping_quotes=True):
    '''
    Keyword arguments:
    start -- where to start (if step is negative go from endbefore-1 to
        start, otherwise go from start to endbefore-1)
    endbefore -- Do not check at or after this value. If negative, start
        from len(haystack)+endbefore which will add a negative and
        subtract from length to obtain the first index to check. If
        step is negative start from endbefore-1. That is why this
        variable is not called "stop" and is not like "stop" in builtin
        Python functions.
    enclosures -- Provide a list of strings, each 2 long, where the
        first character is an opener and the next character is a
        closer. If not None, only find in areas that are neither
        commented nor enclosed. Example: ["()", "[]"]
    allow_quoted -- allow even if within quotes (single or double)
    step -- Move in this direction, normally 1 or -1. If negative,
        go from endbefore-1 to start and check for comment marks
        beforehand (therefore negative step doubles the processing time
        on average).
    min_indent -- The minimum indent used for logging.
    '''
    if step not in [-1, 1]:
        raise ValueError("step must be -1 or 1 not {}.".format(step))
    for quote_mark in quote_marks:
        if len(quote_mark) > 1:
            raise ValueError("Each quote mark can only be 1 in length.")
    result = -1
    closers = {}
    comment_i = -1
    if haystack is None:
        raise ValueError("haystack is None.")
    if needle is None:
        raise ValueError("needle is None.")
    if len(needle) < 1:
        raise ValueError("len(needle) is 0.")
    if comment_delimiters is None:
        comment_delimiters = []
    if endbefore is None:
        endbefore = len(haystack)
    elif endbefore < 0:
        new_endbefore = len(haystack) + endbefore
        # ^ + since already negative
        echo2("{}INFO: endbefore was negative so it will"
              " change to len(haystack)+offset (endbefore={},"
              " new_endbefore={})."
              "".format(min_indent, endbefore, new_endbefore))
        endbefore = new_endbefore
    elif endbefore > len(haystack):
        echo0("{}WARNING: endbefore was too big so it will change to"
              " len(haystack) (endbefore={}, len(haystack)={})."
              "".format(min_indent, endbefore, len(haystack)))
        endbefore = len(haystack)
    if len(haystack) == 0:
        # ^ prevents dubious meaning in ValueError below
        pass
        # echo1("WARNING: haystack length is 0")
        # raise ValueError("haystack length is 0")
        return -1
    elif endbefore < start:
        raise ValueError("{}endbefore is < start which should never be"
                         " the case even if the step is negative"
                         " because in that case the loop iterates from"
                         " endbefore-1 (start={}, endbefore={},"
                         " step={})"
                         "".format(min_indent, start, endbefore, step))
    '''
    q_slices = None
    if (step < 0) and (not allow_quoted):
        q_slices = quoted_slices(haystack, start=start,
                                 endbefore=endbefore)
    '''
    if (step < 0) and (not allow_commented):
        for comment_delimiter in comment_delimiters:
            delI = find_in_code(
                haystack,
                comment_delimiter,
                start=start,
                # endbefore=endbefore
                # ^ never end early to find comment!
                step=1,  # forward to find comment!
                enclosures=None,  # ignore for comment
                allow_quoted=False,  # False for comment
                comment_delimiters=None,  # None since it is the needle now!
                allow_commented=False,
                min_indent=min_indent+"  ",
            )
            if delI >= 0:
                if (comment_i < 0) or (delI < comment_i):
                    comment_i = delI

        if comment_i >= 0:
            if comment_i < endbefore:
                echo1("{}[find_in_code] endbefore will become"
                      " comment_i since the comment is before the"
                      " end (endbefore={}, comment_i={})."
                      "".format(min_indent, endbefore, comment_i))
                endbefore = comment_i

    if enclosures is not None:
        for pair in enclosures:
            if len(pair) != 2:
                raise ValueError("All sets of enclosures must be 2-long"
                                 " but the enclosures are: {}"
                                 "".format(enclosures))
            if len(pair[0]) != 1:
                raise ValueError("All openers must be 1-long"
                                 " but the enclosures are: {}"
                                 "".format(enclosures))
            if len(pair[1]) != 1:
                raise ValueError("All closers must be 1-long"
                                 " but the enclosures are: {}"
                                 "".format(enclosures))
            closers[pair[0]] = pair[1]
    opener_stack = []
    # prev_char = None  # in case step doesn't matter
    left_char = None  # in case step is negative
    # ^ also used in find_unquoted_even_commented
    in_quote = None
    opener_stack = []
    index = start
    if step < 0:
        index = endbefore - 1
    echo2("{}find_in_code(`{}`, '{}':"
          "".format(min_indent, haystack.strip(), needle))
    while ((step > 0 and index <= (endbefore-len(needle)))
            or (step < 0 and (index >= start))):
        this_char = haystack[index:index+1]
        here_c_del = None  # The actual found comment delimiter
        for c_del in comment_delimiters:
            if haystack[index:index+len(c_del)] == c_del:
                here_c_del = c_del
                break
        left_char = None
        if index - 1 >= 0:
            left_char = haystack[index-1:index]
        echo2(min_indent+"{"
              "index:" + str(index) + ";"
              "this_char:" + str(this_char) + ";"
              "in_quote:" + str(in_quote) + ";"
              "opener_stack:" + str(opener_stack) + ";"
              "here_c_del:" + str(here_c_del) + ";"
              "}")
        if in_quote is None:
            needle_i = -1
            if enclosures is not None:
                needle_i = find_which_needle(haystack, index,
                                             needles=enclosures,
                                             subscript=0)
            is_closing = False
            if len(opener_stack) > 0:
                closer = closers[opener_stack[-1]]
                if haystack[index:index+len(closer)] == closer:
                    is_closing = True
            if ((not allow_commented)
                    and ((here_c_del is not None)
                         or (haystack[index:index+3] == '"""')
                         or (haystack[index:index+3] == "'''"))):
                # TODO: handle multi-line comments?
                echo2(min_indent+"END find_in_code with {} due to comment"
                      "".format(result))
                break
            elif this_char in quote_marks:
                # ^ Don't check for escape characters when not
                #   in quotes yet!
                in_quote = this_char
            elif len(opener_stack) > 0:
                if is_closing:
                    opener_stack = opener_stack[:-1]
                elif needle_i > -1:
                    # start a nested parenthetical
                    opener_stack.append(this_char)
            elif needle_i > -1:
                # start a non-nested parenthetical
                opener_stack.append(this_char)
            elif haystack[index:index+len(needle)] == needle:
                # ^ This should only happen when
                #   len(opener_stack) == 0 (it is, since > 0 was
                #   handled in a prior case.
                if len(opener_stack) != 0:
                    raise RuntimeError(
                        "The match should only occur outside of enclosures"
                        " but {} is in {}".format(needle, opener_stack)
                    )
                result = index
                break
        else:
            if (allow_escaping_quotes and (this_char == in_quote)
                    and (left_char != "\\")):
                in_quote = None
            elif haystack[index:index+len(needle)] == needle:
                if allow_quoted:
                    result = index
                    break
        # prev_char = this_char
        index += step
    return result


def find_unquoted_not_commented_not_parenthetical(haystack, needle,
                                                  start=0, endbefore=None,
                                                  step=1,
                                                  comment_delimiters=["#"],
                                                  quote_marks=["'", '"'],
                                                  min_indent="",
                                                  allow_escaping_quotes=True):
    '''
    This function was lost and not found in a previous commit, and may
    have never been created after used. Therefore, 2021-03-13 it was
    re-implemented by calling find_unquoted_not_commented with a new
    enclosures parameter with the value ["()"].
    See find_in_code.
    '''
    return find_in_code(
        haystack,
        needle,
        start=start,
        endbefore=endbefore,
        step=step,
        comment_delimiters=comment_delimiters,
        enclosures=["()"],
        allow_quoted=False,
        quote_marks=quote_marks,
        min_indent=min_indent,
        allow_escaping_quotes=allow_escaping_quotes,
    )


def find_unquoted_not_commented(haystack, needle, start=0, endbefore=None,
                                step=1, comment_delimiters=["#"],
                                quote_marks=['"', "'"],
                                min_indent="",
                                allow_escaping_quotes=True):
    '''
    This function was lost and not found in a previous commit, and may
    have never been created after used. Therefore, 2021-03-13 it was
    re-implemented by calling find_unquoted_not_commented with a new
    enclosures parameter with the value ["()"].
    See find_in_code.
    '''
    return find_in_code(
        haystack,
        needle,
        start=start,
        endbefore=endbefore,
        step=step,
        comment_delimiters=comment_delimiters,
        allow_quoted=False,
        quote_marks=quote_marks,
        min_indent=min_indent,
        allow_escaping_quotes=allow_escaping_quotes,
    )


def find_unquoted_even_commented(haystack, needle, start=0,
                                 endbefore=None, step=1,
                                 comment_delimiters=["#"],
                                 quote_marks=["'", '"'],
                                 min_indent="",
                                 allow_escaping_quotes=True):
    '''
    This function was lost and not found in a previous commit, and may
    have never been created after used. Therefore, 2021-03-13 it was
    re-implemented by calling find_unquoted_not_commented with a new
    enclosures parameter with the value ["()"].
    See find_in_code.
    '''
    return find_in_code(
        haystack,
        needle,
        start=start,
        endbefore=endbefore,
        step=step,
        comment_delimiters=comment_delimiters,
        allow_quoted=False,
        allow_commented=True,
        quote_marks=quote_marks,
        min_indent=min_indent,
        allow_escaping_quotes=allow_escaping_quotes,
    )


def substring_after(haystack, needle):
    needleI = haystack.find(needle)
    if needleI < -1:
        return None
    return haystack[needleI+len(needle):]


def find_after(haystack, needle):
    needleI = haystack.find(needle)
    if needleI < -1:
        return -1
    return needleI+len(needle)


def block_uncomment_line(line, path=None, line_n=None):
    '''
    Keyword arguments:
    path -- The file in which this line exists (for error tracing).
    line_n -- The line number (starting with 1) in path that is where
        this line originated (for error tracing).

    Returns:
    a tuple of line (string), still_commented (boolean).
    '''
    orig_line = line
    still_commented = False
    opener = "/*"
    closer = "*/"
    line_n = 0
    too_many = len(orig_line)
    try_count = 0
    while True:
        try_count += 1
        if try_count >= too_many:
            raise RuntimeError(
                "There were too many tries"
                " (The line `{}` wasn't handled properly"
                " and became `{}` so far)."
                "".format(orig_line, line)
            )
        line_n += 1  # Counting numbers start at 1.
        openI = line.find(opener)
        closeI = -1
        if openI > -1:
            closeI = line.find(closer, openI+len(opener))
        inlineI = line.find("//")
        if openI < 0 and closeI < 0 and inlineI < 0:
            break
        if (openI > -1) and ((inlineI < 0) or (openI < inlineI)):
            # There's a `/*` and either there is no `//` or `/*` is before `//`.
            if closeI > -1:
                if closeI < openI:
                    raise_SyntaxError(
                        path,
                        line_n,
                        'block_uncomment_line only accepts lines that'
                        'were not in a block comment, but there was a'
                        ' {} before {} in `{}`'
                        ''.format(opener, closer, orig_line)
                    )
                echo2('* removing "{}" from "{}"'
                      ''.format(line[openI:closeI+len(closer)], line))
                line = line[:openI] + line[closeI+len(closer):]
            else:
                still_commented = True
        else:
            # There is either no `/*` or there is one to ignore after `//`.
            if inlineI > -1:
                echo2('* removing "{}" from "{}"'
                      ''.format(line[inlineI:], line))
                line = line[:inlineI].strip()
            else:
                raise RuntimeError(
                    "Uh oh, the checks shouldn't happen if there is"
                    " neither a `/*` nor a `//` in a predictable arrangement."
                )

    return line, still_commented


COMMENTED_DEF_WARNING = "comment"


def _try_get_encoded_lines(path, encoding=None):
    # This should be used
    # instead of any function called get_lines (such as from
    # YAMLObject_fromCodeConverter.py) or get_all_lines.

    user_encoding = encoding
    # with open(file, "rb") as ins:
    #     rawdata = ins.read()
    #     det_encoding = chardet.detect(rawdata)['encoding']
    det_encoding = get_file_encoding(path)
    echo1()
    echo1("det_encoding={}".format(det_encoding))

    lines = None
    encodings = [None, 'iso-8859', 'utf-8', 'iso-8859-1', 'latin-1',
                 'cp437']
    # ^ 'cp437' is the (English) Windows Command Prompt's
    #   (The `chcp` command shows code page 437), MIME/IANA: IBM437,
    #   aliases "cp437, 437, csPC8CodePage437, OEM-US"
    #   according to <https://en.wikipedia.org/wiki/Code_page_437>
    #   2022-09-26. It correctly displays German strings (such as the
    #   German spelling of Prusa in Configuration_adv.h in Marlin) read
    #   using binary mode then decoded using "UTF-8".
    if det_encoding not in encodings:
        encodings.insert(0, det_encoding)
    if user_encoding is not None:
        if user_encoding in encodings:
            encodings.remove(user_encoding)
        encodings.insert(0, user_encoding)
    encodingI = 0
    ex0 = None
    echo1('- reading "{}"'.format(path))
    if lines is None:
        while True:
            encoding = encodings[encodingI]
            try:
                lines = []
                if encoding is None:
                    with open(path, 'r', encoding=encoding) as ins:
                        for rawL in ins:
                            '''
                            ^ may cause "UnicodeDecodeError: 'charmap'
                              codec can't" decode byte 0x90 in position
                              5762: character maps to" <undefined>"
                              such as in Marlin bugfix-2.0.x ecaebe4
                              Configuration_adv.h (which Geany says is
                              UTF-8).
                            '''
                            lines.append(rawL)
                else:
                    with open(path, 'r') as ins:
                        for rawL in ins:
                            lines.append(rawL)
                break
            except UnicodeDecodeError as ex:
                if ex0 is None:
                    ex0 = ex
                if "decode byte" in str(ex):
                    encodingI += 1
                    if encodingI >= len(encodings):
                        echo0('\nError reading "{}" (tried encoding={}):'
                              ''.format(path, encoding))
                        raise
                        # raise
                        # break
                    else:
                        echo1("  - encoding={} failed: {}"
                              "".format(encoding, str(ex)))
                        # if encoding is not None:
                        #     raise  # for debug only
                else:
                    echo0('\nError reading "{}" (tried encoding={}):'
                          ''.format(path, encoding))
                    raise
    return lines, encoding


def read_bytes(path):
    with open(path, 'rb') as f:
        return(f.read())
    return None


def try_readlines(path, encoding=None):
    lines = None
    try:
        return _try_get_encoded_lines(path, encoding=encoding)
    except UnicodeDecodeError as ex:
        pass
    with open(path, 'rb') as f:
        f_contents = f.read()
    if encoding is None:
        encoding = DEFAULT_DEC
    contents = f_contents.decode(encoding)
    if "\r\n" in contents:
        contents = contents.replace("\r\n", "\n")
    lines = contents.split("\n")
    echo1("- had to use binary (decoded as {})".format(encoding))
    return lines, "utf-8"


def get_cdef(path, name, lines=None, skip=None, encoding=None,
             line_index=None):
    '''
    Get a value after "#define {}".format(name) in a file located at
    path, and an error.

    Keyword arguments:
    lines -- If this is not None, it is assumed to be a list of lines,
        and path is ignored.
    skip -- Skip this many instances (increase to detect more
        instances). The successive result will be ignored if commented.
    line_index -- Get the value from this line index, and ignore name.
        The index starts at 0 so it is one less than line_n.

    Returns:
    a tuple of value (string), line number (-1 if not found),
        actual_name, and error (string or None).

    Raises:
    UnicodeDecodeError (The implied call to readline in the line iterator
      itself raises the error).
    NotImplementedError if /* is detected inside of an inline comment
    '''
    block_commented = False
    # Account for commented defs:
    commented_v = None
    commented_v_n = -1
    v = None
    v_n = -1
    line_n = 0
    if lines is None:
        lines, got_encoding = try_readlines(path, encoding=encoding)
    count = 0
    actual_name = None
    if name is None:
        if (line_index is None) or (line_index < 0):
            raise ValueError(
                "If you don't provide a variable name, you must provide"
                " a line index (starting at 0 for the first line in the"
                " case of an index as opposed to a line number)."
            )
    for rawL in lines:
        line_n += 1  # Start at 1.
        line = rawL.strip()
        was_commented = False
        if not block_commented:
            inlineI = line.find("//")
            if line.startswith("//"):
                parts = line[2:].strip().split()
                if (skip is not None) and (skip > 0):
                    # Do not uncomment multiple defines or an error
                    # will occur unless enclosed in #ifdef, #elif, etc.
                    continue
                if len(parts) >= 2:
                    if (parts[0] == "#define"):
                        if line_index is not None:
                            if line_index != line_n - 1:
                                continue
                            actual_name = parts[1]
                        else:
                            if (parts[1] != name):
                                continue
                        # Only get this value if the name or line_index
                        #   matches.
                        commented_v_n = line_n
                        commented_v = substring_after(line, name).strip()
                        if commented_v.startswith("//"):
                            commented_v = ""
                        elif "/*" in commented_v:
                            raise NotImplementedError('"/*" in commented value')
                continue
            if inlineI > -1:
                line = line[:inlineI].strip()
        else:
            closeI = line.find("*/")
            if closeI > -1:
                line = line[closeI+2:]
                # in case another comment starts on same line:
                line, block_commented = block_uncomment_line(line)
        if len(line) == 0:
            continue
        parts = line.split()  # spaces/tabs or multiple doesn't matter.
        if ((parts[0] == "#define")
                and ((parts[1] == name) or (line_index == (line_n-1)))):
            count += 1
            if (skip is not None) and (count <= skip):
                echo2("* skipped `{}`".format(rawL.strip()))
                continue
            echo2("* found `{}`".format(rawL.strip()))
            if name is not None:
                v = substring_after(line, name).strip()
            else:
                actual_name = parts[1]
                v = substring_after(line, actual_name).strip()
            v_n = line_n
            break
    if v is None:
        if commented_v is not None:
            echo2('[pycodetool.parsing get_cdef] commented_v="{}"'
                  ''.format(commented_v))
            return commented_v, commented_v_n, actual_name, COMMENTED_DEF_WARNING
    echo2('[pycodetool.parsing get_cdef] v="{}"'
          ''.format(v))
    return v, v_n, actual_name, None


def cdefs_to_d(path, lines=None):
    results = {}
    got_encoding = None
    if lines is None:
        lines, got_encoding = try_readlines(path, encoding=None)
    for i in range(len(lines)):
        line = lines[i]
        v, line_n, got_key, err = get_cdef(
            path,
            None,
            lines=lines,
            line_index=i
        )

        if (err is not None):
            if "commented" in err:
                v = None
            else:
                raise NotImplementedError(
                    'Whether to store cached values when err is'
                    ' "{}" is not decided yet--needs test cases.'
                    ''.format(err)
                )
        if got_key is not None:
            results[got_key] = v
        else:
            echo2('There was no variable in `{}`:'
                  ' The line may be a comment'
                  ' (but not even a commented `#define` apparently)'
                  ''.format(line))
    return results


C_CONSTANTS = ['BOARD_MKS_GEN_L', 'ONBOARD', 'TMC2209', 'A4988',
               'BOARD_BTT_SKR_V1_4_TURBO', 'P0_24_A1']


def set_cdef(path, name, value, comments=None, lines=None,
             encoding=DEFAULT_CO):
    '''
    Set define(s) preserving spacing and comments. If the item is
    commented, uncomment it, unless value is None.

    Sequential arguments:
    path -- the path of the file to read and write (Can be None if using
        lines and you dont want to write to the file) if lines is
        None.
    name -- (string or list/tuple of strings) Look for this value.
        If this is a list, multiple names can be set to the same value
        only reading and writing the file once.
    value -- Set to this value. If None, comment the line and do nothing
        else to it. For a blank define, set "" and the value will be
        uncommented.
    lines -- Provide a list of lines. If path is None, the file will
        not be saved.

    Keyword arguments:
    comments -- (string or list/tuple of strings) Add a comment or list
        of comments after the line. A list is multiline, while a string
        goes at the end of the line. A "//" will be prepended if not
        present unless comments[0] == "/*" and comments[-1] == "*/".

    Returns:
    a tuple containing a list of symbols that changed and a list
    of ECLineInfo objects representing values not changed.
    '''
    names = name
    if (not isinstance(names, list)) and (not isinstance(names, tuple)):
        names = [name]
    name = None

    comment = None
    if (not isinstance(comments, list)) and (not isinstance(comments, tuple)):
        if comments is not None:
            comment = comments
            echo1("* converting {} to list".format(comments))
            comments = [comments]

    if value is None:
        # None forces removing (commenting out) the value further down.
        pass
    elif isinstance(value, str):
        if (len(value) > 1) and value.startswith('"') and value.endswith('"'):
            # It is a string literal.
            pass
        elif (len(value) > 1) and value.startswith('(') and value.endswith(')'):
            # It is a literal formula, hopefully.
            pass
        elif (len(value) > 1) and value.startswith('{') and value.endswith('}'):
            # It is a list or some other valid curly brace initialization
            #   (hopefully).
            pass
        elif value in ["true", "false"]:
            # It is a boolean literal.
            pass
        elif value in C_CONSTANTS:
            # It is a well-known constant.
            pass
        elif len(value) > 0:
            try:
                v = float(value)
            except ValueError as ex:
                echo0("Warning: Non-numerical non-quoted `{}`".format(value))
        # else "" signifies "defined"
    elif value is True:
        value = "true"  # Convert to symbolic ctype
    elif value is False:
        value = "false"  # Convert to symbolic ctype
    elif isinstance(value, int):
        value = str(value)
    elif isinstance(value, float):
        value = str(value)
    else:
        raise TypeError(
            "{} was an unexpected type: {}"
            "".format(name, type(value).__name__)
        )

    do_save = False
    affected_keys = []
    unaffected_items = []
    if lines is None:
        if path is None:
            raise ValueError("You must specify a file and/or lines to modify.")
        # with open(path, 'r') as ins:
            # lines = ins.readlines()
            '''
            ^ readlines may cause "UnicodeDecodeError: 'charmap' codec
              can't decode byte 0x90 in position 5762: character maps to
              <undefined>".
            '''
        lines, got_encoding = try_readlines(path, encoding=encoding)
        do_save = True

    for name in names:
        for skip in range(3):
            # GRID_MAX_POINTS_X appears 3 times in Configuration.h
            #   in Marlin 2.0.x-bugfix branch
            #   (ok since protected under #if, #elif, #elif).
            v, line_n, got_key, err = get_cdef(path, name, lines=lines, skip=skip)
            line_i = line_n - 1
            # COMMENTED_DEF_WARNING is ok (using that line is safe
            #   since the warning indicates there is no non-commented
            #   line with the same name)
            if line_n > -1:
                rawL = lines[line_i]
                original_line = lines[line_i]
                indent_count = len(rawL) - len(rawL.lstrip())
                indent = rawL[:indent_count]
                if value is None:
                    if err == COMMENTED_DEF_WARNING:
                        continue
                    line = indent + "// " + original_line.lstrip()
                    lines[line_i] = line
                    if v is not None:
                        affected_keys.append(name)
                    else:
                        unaffected_items.append(ECLineInfo(
                            name,
                            None,
                            v=v,
                            # t="string",
                            i=line_i,
                            commented=value is None,
                            cm="//",
                            path=path,
                            orphan=True,
                        ))
                    print(line)
                    if get_verbosity() > 0:
                        echo0('* formerly "{}"'.format(original_line))
                    continue
                indent_count = len(rawL) - len(rawL.lstrip())
                indent = rawL[:indent_count]
                line = rawL.strip()
                if line.startswith("//"):
                    line = line[2:].strip()
                parts = line.split()
                line = indent + line
                if parts[0] != "#define":
                    raise RuntimeError('{}:{}: expected #define'
                                       ''.format(path, line_n))
                if v != value:
                    affected_keys.append(name)
                else:
                    unaffected_items.append(ECLineInfo(
                        name,
                        None,
                        v=v,
                        # t="string",
                        i=line_i,
                        commented=value is None,
                        cm="//",
                        path=path,
                        orphan=True,
                    ))

                if v == "":
                    # define the symbol, but do not give it a value.
                    # if len(parts) < 3:
                    #   pass # There is no comment.
                    name_i = line.find(parts[1])
                    if name_i < 0:
                        raise RuntimeError("name wasn't found")
                    original_v_i = name_i + len(parts[1])
                    '''
                    else:
                        comment_i = line.find(parts[2])
                        if comment_i < 0:
                            raise RuntimeError("comment wasn't found")
                        original_v_i = comment_i + len(parts[2])
                    '''
                    detected_sym_name = line[name_i:original_v_i]
                    echo2('detected_sym_name="{}"'.format(detected_sym_name))
                else:
                    original_v_i = line.find(v)
                    echo2('v="{}"'.format(v))
                echo2("original_v_i={}".format(original_v_i))
                after_v_i = original_v_i + len(v)
                echo2("after_v_i={}".format(after_v_i))
                echo2('v="{}"'.format(v))

                # TODO: use raw_cmt_indent and raw_cmt
                raw_cmt = line[after_v_i:]
                raw_cmt_indent_count = len(raw_cmt) - len(raw_cmt.lstrip())
                raw_cmt_indent = raw_cmt[:raw_cmt_indent_count]
                old_cmt = raw_cmt.lstrip()
                this_cmt = raw_cmt
                echo2('this_cmt="{}"'.format(this_cmt))
                if comment is not None:
                    this_cmt = comment
                    if not this_cmt.strip().startswith("//"):
                        this_cmt = "// " + this_cmt
                    if ((not this_cmt[:1].strip() == "")
                            and (raw_cmt_indent_count == 0)):
                        this_cmt = " " + this_cmt
                    # this_cmt += old_cmt
                    # ^ doesn't have space before it
                    this_cmt += raw_cmt
                    # multi-line comments are later (only if comment is None)
                    echo2('this_cmt="{}"'.format(this_cmt))
                old_value = line[original_v_i:after_v_i]
                if old_value != v:
                    raise RuntimeError(
                        "Parsing failed to identify the value in `{}`"
                        "".format(lines[line_i])
                    )
                space_diff = len(value) - len(old_value)
                this_sym = line[:original_v_i]
                post_sym_count = len(this_sym) - len(this_sym.rstrip())
                post_sym = ""
                if post_sym_count > 0:
                    post_sym = this_sym[-post_sym_count:]
                # else leave it blank (Don't start post_sym at 0!)
                this_sym = this_sym.rstrip()
                echo2('value="{}"'.format(value))
                echo2('old_value="{}"'.format(old_value))
                echo2('space_diff="{}"'.format(space_diff))
                echo2('this_sym="{}"'.format(this_sym))
                echo2('post_sym="{}"'.format(post_sym))
                echo2('this_cmt="{}"'.format(this_cmt))
                if space_diff < 0:
                    # add spacing
                    if isnumber(value):
                        post_sym += " "*(-space_diff)
                        echo2('post_sym="{}"'.format(post_sym))
                    else:
                        this_cmt = " "*(-space_diff) + this_cmt
                        echo2('this_cmt="{}"'.format(this_cmt))
                elif space_diff > 0:
                    # remove spacing if available (but leave at least 1)
                    for i in range(space_diff):
                        if value.isdigit() or isnumber(value):
                            echo2("* remove from end of spacing on the left.")
                            # if ((len(post_sym[-2:]) == 2)
                            #         and (post_sym[-2:].strip() == "")):
                            if slice_is_space(post_sym, -2, None):
                                # Only if there are *two* spaces, remove
                                #   one (retain a space to prevent
                                #   mangling the code).
                                post_sym = post_sym[:-1]
                                echo2('* post_sym="{}"'.format(post_sym))
                            else:
                                break
                        else:
                            echo2("* remove from start of spacing on the right")
                            # if ((len(this_cmt[:2]) == 2)
                            #         and (this_cmt[:2].strip() == "")):
                            if slice_is_space(post_sym, None, 2):
                                # Only if there are *two* spaces, remove
                                #   one (retain a space to prevent
                                #   mangling the code).
                                this_cmt = this_cmt[1:]
                                echo2('* this_cmt="{}"'.format(this_cmt))
                            else:
                                break
                # line = line[:original_v_i] + value + line[after_v_i:]
                line = this_sym + post_sym + value + this_cmt
                line = line.rstrip()
                # ^ Remove spacing including if added for shorter values
                lines[line_i] = line
                if line != original_line:
                    print(line)
                    if get_verbosity() > 0:
                        echo0('* changed `{}`\n  to      `{}`'
                              ''.format(original_line.strip(), line.strip()))
                        echo1("  - changed {} to {}".format(v, value))
                CMT_OPENER = "/*"
                if (comment is None) and (comments is not None):
                    block_start_c_i = None
                    block_start = None
                    for c_i in range(len(comments)):
                        this_cmt = comments[c_i]
                        if block_start_c_i is None:
                            if this_cmt.strip().startswith(CMT_OPENER):
                                block_start_c_i = c_i
                                block_start = this_cmt.find(CMT_OPENER)
                        if not this_cmt.strip().startswith("//"):
                            if block_start is None:
                                this_cmt = "// " + this_cmt
                        if not this_cmt.endswith("\n"):
                            this_cmt += "\n"
                        new_c_i = line_i + 1 + c_i
                        if len(lines) <= new_c_i:
                            lines.append(this_cmt)
                        elif lines[new_c_i].strip() != this_cmt:
                            lines.insert(new_c_i, this_cmt)

                        if block_start is not None:
                            if block_start_c_i == c_i:
                                if "*/" in this_cmt[block_start_c_i+len(CMT_OPENER):]:
                                    block_start_c_i = None
                                    block_start = None
                            else:
                                if "*/" in this_cmt:
                                    block_start_c_i = None
                                    block_start = None
            else:
                unaffected_items.append(ECLineInfo(
                    name,
                    None,
                    v=value,
                    # t="string",
                    i=-1,
                    commented=value is None,
                    cm="//",
                    path=path,
                    orphan=True,
                ))
        # if name == "PID_EDIT_MENU":
        #     raise NotImplementedError("preserving comments") # debug only
    if do_save:
        write_lines(path, lines, encoding=encoding)
    return affected_keys, unaffected_items


def write_lines(path, lines, encoding=DEFAULT_CO):
    '''
    Write each line in lines to path (Only each line not
    ending with "\n" gets that added).
    '''
    if encoding == "utf_8":
        encoding = "utf-8"
    echo1('write_lines...encoding="{}"...'.format(encoding))
    # raise NotImplementedError()
    # with open(path, 'w', encoding=encoding) as outs:
    faux_path = os.path.join(DATA_DIR, "faux-words")
    real_path = os.path.join(DATA_DIR, "real-words")
    real_pairs = []
    for sub in os.listdir(faux_path):
        fauxStrPath = os.path.join(faux_path, sub)
        realStrPath = os.path.join(real_path, sub)
        fauxBytes = read_bytes(fauxStrPath)
        realBytes = read_bytes(realStrPath)
        real_pairs.append((fauxBytes, realBytes))
    with open(path, 'wb') as outs:
        for rawL in lines:
            if not rawL.endswith("\n"):
                rawL += "\n"
            try:
                rawLB = rawL.encode(encoding)
                for (fauxBytes, realBytes) in real_pairs:
                    rawLB = rawLB.replace(fauxBytes, realBytes)
                outs.write(rawLB)
            except UnicodeEncodeError:
                echo0('\nError: Encoding "{}" failed:'.format(rawL))
                raise
    return True


def find_non_whitespace(haystack, start, step=1):
    if step not in [-1, 1]:
        raise ValueError("step must be -1 or 1 not {}.".format(step))
    i = start - step
    while True:
        i += step
        if step < 1:
            if i < 0:
                break
        else:
            if i >= len(haystack):
                break
        if haystack[i].strip() == haystack[i]:
            return i
    return -1


def find_whitespace(haystack, start, step=1):
    if step not in [-1, 1]:
        raise ValueError("step must be -1 or 1 not {}.".format(step))
    i = start - step
    while True:
        i += step
        if step < 1:
            if i < 0:
                break
        else:
            if i >= len(haystack):
                break
        if haystack[i].strip() != haystack[i]:
            return i
    return -1


def insert_lines(path, new_lines, lines=None, after=None, before=None,
                 encoding=DEFAULT_CO):
    '''
    Insert new_lines (value, or list/tuple of values) into file,
    inserting newline characters automatically if not in new_lines.

    Keyword arguments:
    path -- Write to this path if lines is None.
    after -- Insert new_lines after the first instance of this flag
        (or if this and after are both None, at the start of the file).
    before -- Insert new_lines before the first instance of this flag
        (or if this and before are both None, at the start of the file).
    lines -- If not None, use this list as the contents and ignore path
        (and don't save except to lines).
    encoding -- Use this encoding when writing strings to the file. If
        the file path is loaded an encoding can be detected from it,
        that encoding will be used instead of the specified encoding.

    Returns:
    True if success, False if failed.
    '''
    flag = None
    move_flag = None
    if before is not None:
        if after is not None:
            raise ValueError("You can only specify before or after, not both.")
        flag = before
        move_flag = True
    elif after is not None:
        flag = after
        move_flag = False

    if (not isinstance(new_lines, list)) and (not isinstance(new_lines, tuple)):
        if new_lines is None:
            raise ValueError("new_lines is None")
        new_lines = [new_lines]
    do_save = False
    if lines is None:
        if path is None:
            raise ValueError("You must specify a file and/or lines to modify.")
        lines, got_encoding = try_readlines(path, encoding=encoding)
        if got_encoding is not None:
            encoding = got_encoding
        do_save = True
    line_n = 0

    start = -1

    line_i = -1
    for rawL in lines:
        line_n += 1  # Start at 1.
        line_i += 1  # Start at 0.
        line = rawL.strip()
        if (flag is not None) and (len(flag) > 0):
            if flag in rawL:
                if start < 0:
                    if move_flag:
                        # `before` was specified, so move the flag
                        #   value forward to make room (place new_lines
                        #   before it).
                        start = line_i
                    else:
                        start = line_i + 1
    if start < 0:
        if flag is not None:
            return False
        else:
            start = 0
            echo2('[pycodetool.parsing insert_lines]'
                  ' after/before was not set so inserting at line {}'
                  ''.format(start+1))
    echo2("start={}".format(start))
    # raise NotImplementedError("insert if not found")
    insert_i = start - 1  # - 1 since incremented below
    for i in range(len(new_lines)):
        insert_i += 1
        lines.insert(insert_i, new_lines[i])
    if do_save:
        write_lines(path, lines, encoding=encoding)
    return True


def get_file_bom_encoding(filename):
    # from <https://stackoverflow.com/a/44405580>
    with open(filename, 'rb') as openfileobject:
        line = str(openfileobject.readline())
        if line[2:14] == str(codecs.BOM_UTF8).split("'")[1]:
            return 'utf_8'
        if line[2:10] == str(codecs.BOM_UTF16_BE).split("'")[1]:
            return 'utf_16'
        if line[2:10] == str(codecs.BOM_UTF16_LE).split("'")[1]:
            return 'utf_16'
        if line[2:18] == str(codecs.BOM_UTF32_BE).split("'")[1]:
            return 'utf_32'
        if line[2:18] == str(codecs.BOM_UTF32_LE).split("'")[1]:
            return 'utf_32'
    return ''


def get_all_file_encodings(filename):
    # from <https://stackoverflow.com/a/44405580>
    encoding_list = []
    encodings = ('utf_8', 'utf_16', 'utf_16_le', 'utf_16_be',
                 'utf_32', 'utf_32_be', 'utf_32_le',
                 'cp850', 'cp437', 'cp852', 'cp1252', 'cp1250', 'ascii',
                 'utf_8_sig', 'big5', 'big5hkscs', 'cp037', 'cp424', 'cp500',
                 'cp720', 'cp737', 'cp775', 'cp855', 'cp856', 'cp857',
                 'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864',
                 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932',
                 'cp949', 'cp950', 'cp1006', 'cp1026', 'cp1140', 'cp1251',
                 'cp1253', 'cp1254', 'cp1255', 'cp1256', 'cp1257',
                 'cp1258', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213',
                 'euc_kr', 'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp',
                 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004',
                 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 'latin_1',
                 'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5',
                 'iso8859_6', 'iso8859_7', 'iso8859_8', 'iso8859_9',
                 'iso8859_10', 'iso8859_13', 'iso8859_14', 'iso8859_15',
                 'iso8859_16', 'johab', 'koi8_r', 'koi8_u', 'mac_cyrillic',
                 'mac_greek', 'mac_iceland', 'mac_latin2', 'mac_roman',
                 'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004',
                 'shift_jisx0213'
                 )
    for e in encodings:
        try:
            fh = codecs.open(filename, 'r', encoding=e)
            fh.readlines()
        except UnicodeDecodeError:
            fh.close()
        except UnicodeError:
            fh.close()
        else:
            encoding_list.append([e])
            fh.close()
            continue
    return encoding_list


def get_file_encoding(filename):
    # from <https://stackoverflow.com/a/44405580>
    file_encoding = get_file_bom_encoding(filename)
    if file_encoding != '':
        return file_encoding
    encoding_list = get_all_file_encodings(filename)
    file_encoding = str(encoding_list[0][0])
    if file_encoding[-3:] == '_be' or file_encoding[-3:] == '_le':
        file_encoding = file_encoding[:-3]
    return file_encoding
