#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
me = "pycodetool.parsing"
"""
Parse data and manipulate variables.
"""
# Copyright (C) 2018 Jake Gustafson

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


import os
import sys
import traceback
import copy
try:
    input = raw_input
except NameError:
    pass

verbose_enable = False
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


def set_verbose(on):
    global verbose_enable
    verbose_enable = on


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
        input if a variable does not exist. If default_value is None,
        do not add the variable to _data if not entered.
        """
        is_changed = False
        if name not in self._data:
            print("")
            if default_value is None:
                print("WARNING: this program does not have a"
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
            print("Using " + name + " '" + self._data[name] + "'")
            is_changed = True

        if not os.path.isfile(self._config_path):
            is_changed = True
            print("Creating '"+self._config_path+"'")
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
            print("[ ConfigManager ] WARNING to developer: run"
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
    [copied to install_any.py in linux-preinstall by author]
    Show the values if they differ before the assertion error stops the
    program.

    Keyword arguments:
    tbs -- traceback string (either caller or some sort of message to
           show to describe what data produced the arguments if they're
           derived from something else)
    '''
    if ((v1 is True) or (v2 is True) or (v1 is False) or (v2 is False)
            or (v1 is None) or (v2 is None)):
        if v1 is not v2:
            print("")
            print("{} is not {}".format(toPythonLiteral(v1),
                                        toPythonLiteral(v2)))
            if tbs is not None:
                print("for {}".format(tbs))
        assert(v1 is v2)
    else:
        if v1 != v2:
            print("")
            print("{} != {}".format(toPythonLiteral(v1),
                                    toPythonLiteral(v2)))
            if tbs is not None:
                print("while {}".format(tbs))
        assert(v1 == v2)


def assertAllEqual(list1, list2, tbs=None):
    '''
    [copied to install_any.py in linux-preinstall by author]
    '''
    if len(list1) != len(list2):
        print("The lists are not the same length: list1={}"
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
        pass
    else:
        raise ValueError("old_dict is None.")
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
                print("[ {} ts_equals ] WARNING: Types differ for {}."
                      " v1 is {} and v2 is {}"
                      "".format(me, tb, type(v1).__name__,
                                type(v2).__name__))
        return False
    if type(v1).__name__ == "bool":
        return v1 is v2
    return v1 == v2


def is_dict_subset(new_dict, old_dict, verbose_messages_enable,
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
            if verbose_messages_enable:
                print("SAVING '" + verbose_dest_description
                      + "' since " + str(this_key)
                      + " not in saved version.")
            break
        elif not ts_equals(new_dict[this_key], old_dict[this_key],
                           tb=this_key+" in is_dict_subset for "+tb):
            is_changed = True
            if verbose_messages_enable:
                print("SAVING '" + verbose_dest_description
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
        print(min_indent+"print_file: path is None")
        return 0
    if not os.path.isfile(path):
        print(min_indent+"print_file: file does not exist")
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
    except PermissionError:
        print(min_indent+"print_file: could not read {}".format(path))
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
    # print("Checking "+str(path)+" for settings...")
    if (results is None) or (type(results) is not dict):
        results = {}
    if os.path.isfile(path):
        print("[ ConfigManager ] Using existing '" + path + "'")
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
            if strp[0] == comment_delimiter:
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
            # print("   CHECKING... " + result_name
            #       + ":"+result_val)
            if ((result_name not in results) or
                    (results[result_name] != result_val)):
                entries_modified_count += 1
                # print(str(entries_modified_count))
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
        print("Could not finish saving chunk metadata to '" + str(path)
              + "': " + str(traceback.format_exc()))
        print(e)


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
            print("'" + debug_src_name + "' has bad position data--"
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
        print("error in is_allowed_in_variable_name_char: one_char"
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


def explode_unquoted(haystack, delimiter):
    elements = list()
    while True:
        index = find_unquoted_not_commented(haystack, delimiter)
        if index >= 0:
            elements.append(haystack[:index])
            haystack = haystack[index+1:]
        else:
            break
    elements.append(haystack)
    # ^ rest of haystack is the param after
    #   last comma, else beginning if none
    return elements

def find_dup(this_list, discard_whitespace_ignore_None_enable=True,
             ignore_list=None, ignore_numbers_enable=False):
    result = -1
    """DISCARDS whitespace, and never matches None to None"""
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
                            if verbose_enable:
                                print("[" + str(i1) + "]:"
                                      + str(this_list[i1])
                                      + " matches [" + str(i2) + "]:"
                                      + str(this_list[i2]))
                            break
            if result > -1:
                break
    else:
        print("[ parsing.py ] ERROR in has_dups: " + str(this_list)
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
            print("ERROR in get_initial_value_from_conf: '" + str(path)
                  + "' is not a file.")
    else:
        print("ERROR in get_initial_value_from_conf: path is None.")
    return result


def find_which_needle(haystack, haystack_i, needles, subscript=None):
    '''
    Get the index in needles that exists at haystack[haystack_i:] or
    -1 if no needles are there.

    Keyword arguments:
    subscript -- if each needle is subscriptable, subscript it with
                 subscript before using it. Otherwise (if None) each
                 element of needle will be used directly as usual.
                 Example: if needles is ["()", "{}"] then set
                 subscript=0 to look for only "(" and "{".
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
    Sequential arguments:
    v -- Check for this index within each range
    ranges -- A list of number pairs such as tuples [(start, stop),...]
              where start is inclusive and stop is exclusive as per
              Python slice and range notation.

    Keyword arguments:
    length -- If either of the values in any range is negative, you must
              provide the length of the string to which the slices
              refer (so that the real index can be calculated).
              Otherwise this function will raise a ValueError.

    returns:
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
                  comment_delimiter="#"):
    '''
    Get a list of tuples where each tuple is the start and stop values
    for quoted portions of haystack. The first entry of the tuple is
    the first quotation mark (`"` or `'`) and the second entry of
    the tuple is 1 after the ending quote's index (as per slice
    notation).

    Keyword arguments:
    comment_delimiter -- Set a comment delimiter of any length to
                         prevent detections at or after the character.
                         Any comment_delimiter before the start is
                         ignored.
    '''
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
        if verbose_enable:
            print("INFO: endbefore was negative so it will"
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
    while i+1 < endbefore:
        i += 1
        if verbose_enable:
            print("(i={}, open_i={},".format(i, open_i))
        c = haystack[i]
        if verbose_enable:
            print(" c={})".format(c))
        if open_i is None:
            if c in quotes:
                open_i = i
            elif (haystack[i:i+len(comment_delimiter)]
                    == comment_delimiter):
                break
        elif (c == haystack[open_i]) and (prev_c != "\\"):
            results.append((open_i, i+1))
            # ^ first quote & 1 after end quote as per slice notation
            #   (including both quotes)
            open_i = None
        prev_c = c
    if open_i is not None:
        quoted_slices_error = END_BEFORE_QUOTE_ERR
        print("WARNING: The following line ended at {} before the quote"
              " at column {} ended (endbefore={}):`{}`"
              "".format(i, open_i+1, endbefore, haystack))
    return results


def find_in_code(haystack, needle, start=0, endbefore=None,
                   step=1, comment_delimiter="#",
                   enclosures=None, allow_quoted=True,
                   allow_commented=False):
    '''
    Keyword arguments:
    start -- where to start (if step is negative go from endbefore-1 to
             start, otherwise go from start to endbefore-1)
    endbefore -- Do not check at or after this value. If negative, start
                 from len(haystack)+endbefore which will add a negative
                 and subtract from length to obtain the first index to
                 check. If step is negative start from endbefore-1. That
                 is why this variable is not called "stop" and is not
                 like "stop" in builtin Python functions.
    enclosures -- Provide a list of strings, each 2 long, where the
                  first character is an opener and the next character
                  is a closer. If not None, only find in areas that are
                  neither commented nor enclosed. Example:
                  ["()", "[]"]
    allow_quoted -- allow even if within quotes (single or double)
    step -- Move in this direction, normally 1 or -1. If negative,
            go from endbefore-1 to start and check for comment marks
            beforehand (therefore negative step doubles the processing
            time on average).
    '''
    result = -1
    closers = {}
    comment_i = -1
    if step == 0:
        raise ValueError("step is 0")
    if endbefore > len(haystack):
        print("WARNING: endbefore was too big so it will change to"
              " len(haystack) (endbefore={}, len(haystack)={})."
              "".format(endbefore, len(haystack)))
        endbefore = len(haystack)
    if endbefore is None:
        endbefore = len(haystack)
    elif endbefore < 0:
        new_endbefore = len(haystack) + endbefore
        # ^ + since already negative
        if verbose_enable:
            print("INFO: endbefore was negative so it will"
                  " change to len(haystack)+offset (endbefore={},"
                  " new_endbefore={})."
                  "".format(endbefore, new_endbefore))
        endbefore = new_endbefore
    if len(haystack) == 0:
        # ^ prevents dubious meaning in ValueError below
        pass
        # print("WARNING: haystack length is 0")
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
        comment_i = find_in_code(haystack, comment_delimiter,
                                 start=0,
                                 # endbefore=endbefore
                                 # ^ never end early to find comment!
                                 step=1, # forward to find comment!
                                 enclosures=None, # ignore for comment
                                 allow_quoted=False, # False for comment
                                 comment_delimiter=None,
                                 # ^ None since it is the needle now
                                 allow_commented=False)
        if comment_i >= 0:
            if comment_i < endbefore:
                if verbose_enable:
                    print("[find_in_code] endbefore will become"
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
        if verbose_enable:
            print("    find_in_code in "
                  + haystack.strip() + ":")
        while ((step > 0 and index <= (endbefore-len(needle))) or
               (step < 0 and (index >= start))):
            this_char = haystack[index:index+1]
            left_char = None
            if index - 1 >= 0:
                left_char = haystack[index-1:index]
            if verbose_enable:
                print("      {"
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
                        and ((this_char == comment_delimiter)
                             or (haystack[index:index+3] == '"""')
                             or (haystack[index:index+3] == "'''"))
                    ):
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
    start=0, endbefore=-1, step=1, comment_delimiter="#"):
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
        comment_delimiter=comment_delimiter,
        enclosures=["()"],
        allow_quoted=False,
    )


def find_unquoted_not_commented(haystack, needle,
    start=0, endbefore=-1, step=1, comment_delimiter="#"):
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
        comment_delimiter=comment_delimiter,
        allow_quoted=False,
    )

def find_unquoted_even_commented(haystack, needle,
    start=0, endbefore=-1, step=1, comment_delimiter="#"):
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
        comment_delimiter=comment_delimiter,
        allow_quoted=False,
        allow_commented=True,
    )
