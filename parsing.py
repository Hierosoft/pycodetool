#!/usr/bin/env python3
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

from __future__ import division

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


class InstalledFile:
    source_dir_path = None
    dest_dir_path = None
    file_name = None

    def __init__(self, file_name, source_dir_path, dest_dir_path):
        self.file_name = file_name
        self.source_dir_path = source_dir_path
        self.dest_dir_path = dest_dir_path


class ConfigManager:
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

    def get_var(self, name):
        result = None
        if name in self._data:
            result = self._data[name]
        return result

    def save_yaml(self):
        save_conf_from_dict(self._config_path, self._data, self._ao,
                            save_nulls_enable=False)


def get_dict_deepcopy(old_dict):
    new_dict = None
    if type(old_dict) is dict:
        new_dict = {}
        for this_key in old_dict:
            new_dict[this_key] = copy.deepcopy(old_dict[this_key])
    return new_dict


def is_dict_subset(new_dict, old_dict, verbose_messages_enable,
                   verbose_dest_description="unknown file"):
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
        elif new_dict[this_key] != old_dict[this_key]:
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
        for try_vec in this_list:
            if try_vec[0] == this_vec[0] and try_vec[1] == this_vec[1]:
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


# Finds needle in haystack where not quoted, taking into account escape
#   sequence for single-quoted or double-quoted string inside haystack.
def find_unquoted_even_commented(haystack, needle, start=0,
                                 endbefore=-1, step=1):
    result = -1

    prev_char = None
    if ((haystack is not None) and (needle is not None) and
            (len(needle) > 0)):
        in_quote = None
        if endbefore > len(haystack):
            endbefore = len(haystack)
        if endbefore < 0:
            endbefore = len(haystack)
        index = start
        if step < 0:
            index = endbefore - 1
        if verbose_enable:
            print("    find_unquoted_not_commented in "
                  + haystack.strip() + ":")
        while ((step > 0 and index <= (endbefore-len(needle))) or
               (step < 0 and (index >= 0))):
            this_char = haystack[index:index+1]
            if verbose_enable:
                print("      {"
                      + "index:" + str(index) + ";"
                      + "this_char:" + str(this_char) + ";"
                      + "in_quote:" + str(in_quote) + ";"
                      + "}")
            if in_quote is None:
                if (this_char == '"') or (this_char == "'"):
                    in_quote = this_char
                elif haystack[index:index+len(needle)] == needle:
                    result = index
                    break
            else:
                if (this_char == in_quote) and (prev_char != "\\"):
                    in_quote = None
                elif haystack[index:index+len(needle)] == needle:
                    result = index
                    break
            prev_char = this_char
            index += step
    return result


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


def find_unquoted_not_commented(haystack, needle, start=0, endbefore=-1,
                                step=1, comment_delimiter="#"):
    result = -1

    prev_char = None
    if ((haystack is not None) and
            (needle is not None) and
            (len(needle) > 0)):
        in_quote = None
        if endbefore > len(haystack):
            endbefore = len(haystack)
        if endbefore < 0:
            endbefore = len(haystack)
        index = start
        if step < 0:
            index = endbefore - 1
        if verbose_enable:
            print("    find_unquoted_not_commented in "
                  + haystack.strip() + ":")
        while ((step > 0 and index <= (endbefore-len(needle))) or
               (step < 0 and (index >= 0))):
            this_char = haystack[index:index+1]
            if verbose_enable:
                print("      {"
                      + "index:" + str(index) + ";"
                      + "this_char:" + str(this_char) + ";"
                      + "in_quote:" + str(in_quote) + ";"
                      + "}")
            if in_quote is None:
                if (this_char == comment_delimiter) or \
                        (haystack[index:index+3] == "\"\"\""):
                    break
                elif (this_char == '"') or (this_char == "'"):
                    in_quote = this_char
                elif haystack[index:index+len(needle)] == needle:
                    result = index
                    break
            else:
                if (this_char == in_quote) and (prev_char != "\\"):
                    in_quote = None
                elif haystack[index:index+len(needle)] == needle:
                    result = index
                    break
            prev_char = this_char
            index += step
    return result

