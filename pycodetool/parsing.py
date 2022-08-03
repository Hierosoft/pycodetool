#!/usr/bin/env python
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

from pycodetool import (
    echo0,
    echo1,
    echo2,
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
              source_path=None, line_n=None):
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
        open_paren_i = find_unquoted_not_commented(line, "(")
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


def toPythonLiteral(v):
    '''
    [copied to install_any.py in linux-preinstall by author]
    '''
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
    use the self.assertEqual from super instead of this.

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
        assert(v1 is v2)
    else:
        if v1 != v2:
            echo0("")
            echo0("{} != {}".format(toPythonLiteral(v1),
                                    toPythonLiteral(v2)))
            if tbs is not None:
                echo0("while {}".format(tbs))
        assert(v1 == v2)


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
    try:
        float(s)
        return True
    except ValueError:
        return False


def view_traceback(min_indent=""):
    ex_type, ex, tb = sys.exc_info()
    print(min_indent+str(ex_type))
    print(min_indent+str(ex))
    traceback.print_tb(tb)
    del tb


def print_file(path, min_indent=""):
    line_count = 0
    if path is None:
        echo0(min_indent+"print_file: path is None")
        return 0
    if not os.path.isfile(path):
        echo0(min_indent+"print_file: file does not exist")
        return 0
    try:
        if min_indent is None:
            min_indent = ""
        ins = open(path, 'r')
        rawl = True
        while rawl:
            rawl = ins.readline()
            line_count += 1
            if rawl:
                print(min_indent+rawl)
        ins.close()
        # if line_count == 0:
        #     print(min_indent + "print_file WARNING: "
        #           + str(line_count)+" line(s) in '"+path+"'")
        # else:
        #     print(min_indent + "# " + str(line_count)
        #           + " line(s) in '" + path + "'")
    except PermissionError as ex:
        echo0(min_indent+'print_file: could not read "{}": {}'
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
                     strip=True):
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
    '''
    elements = list()
    start = 0
    echo2("explode_unquoted:")
    while True:
        index = find_unquoted_not_commented(haystack, delimiter,
                                            start=start)
        echo2('- substring haystack[{}:]="{}"'
              ''.format(start, haystack[start:]))
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
            break

    element = haystack[start:].strip() if strip else haystack[start:]
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
    similar but also uses field delimiters.
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
                 allow_commented=False):
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
    '''
    result = -1
    closers = {}
    comment_i = -1
    if comment_delimiters is None:
        comment_delimiters = []
    if step == 0:
        raise ValueError("step is 0")
    if endbefore is None:
        endbefore = len(haystack)
    if endbefore > len(haystack):
        echo0("WARNING: endbefore was too big so it will change to"
              " len(haystack) (endbefore={}, len(haystack)={})."
              "".format(endbefore, len(haystack)))
        endbefore = len(haystack)
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
    if len(haystack) == 0:
        # ^ prevents dubious meaning in ValueError below
        pass
        # echo1("WARNING: haystack length is 0")
        # raise ValueError("haystack length is 0")
        return -1
    elif endbefore < start:
        raise ValueError("endbefore is < start which should never be"
                         " the case even if the step is negative"
                         " because in that case the loop iterates from"
                         " endbefore-1 (start={}, endbefore={},"
                         " step={})"
                         "".format(start, endbefore, step))
    q_slices = None
    if (step < 0) and (not allow_quoted):
        q_slices = quoted_slices(haystack, start=start,
                                 endbefore=endbefore)
    if (step < 0) and (not allow_commented):
        for comment_delimiter in comment_delimiters:
            delI = find_in_code(haystack, comment_delimiter,
                                start=0,
                                # endbefore=endbefore
                                # ^ never end early to find comment!
                                step=1,  # forward to find comment!
                                enclosures=None,  # ignore for comment
                                allow_quoted=False,  # False for comment
                                comment_delimiters=None,
                                # ^ None since it is the needle now
                                allow_commented=False)
            if delI >= 0:
                if (comment_i < 0) or (delI < comment_i):
                    comment_i = delI

        if comment_i >= 0:
            if comment_i < endbefore:
                echo1("[find_in_code] endbefore will become"
                      " comment_i since the comment is before the"
                      " end (endbefore={}, comment_i={})."
                      "".format(endbefore, comment_i))
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
    if ((haystack is not None) and
            (needle is not None) and
            (len(needle) > 0)):
        in_quote = None
        opener_stack = []
        index = start
        if step < 0:
            index = endbefore - 1
        echo2("    find_in_code in "
              + haystack.strip() + ":")
        while ((step > 0 and index <= (endbefore-len(needle))) or
               (step < 0 and (index >= start))):
            this_char = haystack[index:index+1]
            here_c_del = None
            for c_del in comment_delimiters:
                if haystack[index:index+len(c_del)] == c_del:
                    here_c_del = c_del
                    break
            left_char = None
            if index - 1 >= 0:
                left_char = haystack[index-1:index]
            echo2("      {"
                  "index:" + str(index) + ";"
                  "this_char:" + str(this_char) + ";"
                  "in_quote:" + str(in_quote) + ";"
                  "opener_stack:" + str(opener_stack) + ";"
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
                    break
                elif (this_char == '"') or (this_char == "'"):
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
                    result = index
                    break
            else:
                if (this_char == in_quote) and (left_char != "\\"):
                    in_quote = None
                elif haystack[index:index+len(needle)] == needle:
                    if allow_quoted:
                        result = index
                        break
            # prev_char = this_char
            index += step
    return result


def find_unquoted_not_commented_not_parenthetical(haystack, needle,
                                                  start=0, endbefore=-1,
                                                  step=1,
                                                  comment_delimiters=["#"]):
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
    )


def find_unquoted_not_commented(haystack, needle, start=0, endbefore=-1,
                                step=1, comment_delimiters=["#"]):
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
    )


def find_unquoted_even_commented(haystack, needle, start=0,
                                 endbefore=-1, step=1,
                                 comment_delimiters=["#"]):
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
    )
