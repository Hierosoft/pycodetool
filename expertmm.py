import os
import sys
import traceback

verbose_enable = False


#formerly pcttext:
#uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#lowercase_chars = uppercase_chars.lower()
#letter_chars = uppercase_chars+lowercase_chars
digit_chars = "0123456789"
#identifier_chars = letter_chars+"_"+digit_chars
#identifier_and_dot_chars = identifier_chars + "."

#formerly from expertmmregressionsuite:
alpha_upper_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
alpha_lower_chars = alpha_upper_chars.lower()
alpha_chars = alpha_upper_chars+alpha_lower_chars
#numeric_chars = "1234567890"
alnum_chars = alpha_chars+digit_chars
identifier_chars = alnum_chars+"_"

class InstalledFile:
    source_dir_path = None
    dest_dir_path = None
    file_name = None

    def __init__(self, file_name, source_dir_path, dest_dir_path):
        self.file_name=file_name
        self.source_dir_path=source_dir_path
        self.dest_dir_path=dest_dir_path

class ConfigManager:
    #config_name = None
    _config_path = None
    _data = None
    _ao = None

    #DOES load variables if path exists
    def __init__(self, config_file_path, assignment_operator_string):
        self._data = {}
        self._config_path = config_file_path
        self._ao = assignment_operator_string
        self._data = get_dict_modified_by_conf_file(self._data, self._config_path, self._ao)

    #DOES ask for user input if does not exist. If default_value is none, do not add to _data if not given
    def load_var_or_ask_console_input(self, name, default_value, description):
        is_changed = False
        if name not in self._data:
            print("")
            if default_value is None:
                print("WARNING: this program does not have a default value for "+name+".")
                default_value = ""
            answer = raw_input("Please enter "+description+" ("+name+") [blank for "+default_value+"]: ")
            if answer is not None:
                answer = answer.strip()

            if answer is not None and len(answer)>0:
                self._data[name] = answer
            else:
                self._data[name] = default_value
            print("Using "+name+" '"+self._data[name]+"'")
            is_changed = True

        if not os.path.isfile(self._config_path):
            is_changed = True
            print("Creating '"+self._config_path+"'")
        if is_changed:
            self.save_yaml()

    def prepare_var(self, name, default_value, description):
        self.load_var_or_ask_console_input(name, default_value, description)

    def contains(self, name):
        return (name in self._data.keys())

    def remove_var(self, name):
        try:
            del self._data[name]
            self.save_yaml()
        except KeyError:
            pass

    #DOES autosave IF different val
    def set_var(self, name, val):
        is_changed = False
        if name not in self._data.keys():
            print("WARNING to developer: run prepare_var before set_val, so that variable has a default.")
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
        save_conf_from_dict(self._config_path, self._data, self._ao, save_nulls_enable=False)

def get_dict_deepcopy(old_dict):
    new_dict = None
    if type(old_dict) is dict:
        new_dict = {}
        for this_key in old_dict.iterkeys():
            new_dict[this_key] = old_dict[this_key]
    return new_dict

def is_dict_subset(new_dict, old_dict, verbose_messages_enable, verbose_dest_description="unknown file"):
    is_changed = False
    try:
        if old_dict is not None:
            if new_dict is not None:
                old_dict_keys = old_dict.keys()
                for this_key in new_dict.iterkeys():
                    if (this_key not in old_dict_keys):
                        is_changed = True
                        if verbose_messages_enable:
                            print("SAVING '"+verbose_dest_description+"' since "+str(this_key)+" not in saved version.")
                        break
                    elif new_dict[this_key] != old_dict[this_key]:
                        is_changed = True
                        if verbose_messages_enable:
                            print("SAVING '"+verbose_dest_description+"' since "+str(this_key)+" not same as saved version.")
                        break
            #else new_dict is None so no change detected (no new information)
        else:
            if new_dict is not None:
                is_changed = True
    except:
        print("Could not finish is_dict_subset:")
        view_traceback()
    return is_changed

def ivec2_equals(pos1, pos2):
    return (int(pos1[0])==int(pos2[0])) and (int(pos1[1])==int(pos2[1]))

def get_dict_from_conf_file(path,assignment_operator="="):
    results = None
    results = get_dict_modified_by_conf_file(results, path, assignment_operator)
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

def view_traceback():
    ex_type, ex, tb = sys.exc_info()
    print(str(ex_type))
    print(str(ex))
    traceback.print_tb(tb)
    del tb

def print_file(path, min_indent=""):
    line_count = 0
    try:
        if path is not None:
            if os.path.isfile(path):

                if min_indent is None:
                    min_indent = ""
                ins = open(path, 'r')
                line = True
                while line:
                    line = ins.readline()
                    line_count += 1
                    if line:
                        print(min_indent+line)
                ins.close()
                #if line_count==0:
                    #print(min_indent+"print_file WARNING: "+str(line_count)+" line(s) in '"+path+"'")
                #else:
                    #print(min_indent+"# "+str(line_count)+" line(s) in '"+path+"'")
            else:
                print (min_indent+"print_file: file does not exist")
        else:
            print (min_indent+"print_file: path is None")
    except:
        print(min_indent+"print_file: could not finish")
        try:
            ins.close()
        except:
            pass
    return line_count

def get_dict_modified_by_conf_file(this_dict, path, assignment_operator="=", comment_delimiter="#", inline_comments_enable=False):
    results = this_dict
    #print ("Checking "+str(path)+" for settings...")
    if (results is None) or (type(results) is not dict):
        results = {}
    if os.path.isfile(path):
        ins = open(path, 'r')
        line = True
        while line:
            line = ins.readline()
            if line and len(line)>0:
                line_strip=line.strip()
                if len(line_strip)>0 and line_strip[0]!=comment_delimiter:  # if not comment
                    if not line_strip[0]=="-":  # ignore yaml arrays
                        if inline_comments_enable:
                            comment_index = line_strip.find(comment_delimiter)
                        ao_index = line_strip.find(assignment_operator)
                        if ao_index>=1:  # intentionally skip zero-length variable names
                            if ao_index<len(line_strip)-1:  # skip yaml implicit nulls or yaml objects
                                result_name = line_strip[:ao_index].strip()
                                result_value = line_strip[ao_index+1:].strip()
                                result_lower = result_value.lower()
                                if result_value=="None" or result_value=="null" or result_value=="~" or result_value=="NULL":
                                    result_value = None
                                elif result_lower=="true":
                                    result_value = True
                                elif result_lower=="false":
                                    result_value = False
                                elif RepresentsInt(result_value):
                                    result_value = int(result_value)
                                elif RepresentsFloat(result_value):
                                    result_value = float(result_value)
                                #print ("   CHECKING... "+result_name+":"+result_value)
                                results[result_name]=result_value
        ins.close()
    return results

def save_conf_from_dict(path, this_dict, assignment_operator="=", save_nulls_enable=True):
    try:
        outs = open(path, 'w')
        for this_key in this_dict.keys():
            if save_nulls_enable or (this_dict[this_key] is not None):
                if this_dict[this_key] is None:
                    outs.write(this_key+assignment_operator+"null\n")
                else:
                    outs.write(this_key+assignment_operator+str(this_dict[this_key])+"\n")
        outs.close()
    except:
        print("Could not finish saving chunk metadata to '"+str(path)+"': "+str(traceback.format_exc()))
        try:
            outs.close()
        except:
            pass

def get_tuple_from_notation(line, debug_src_name="<unknown object>"):
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
            except:
                player_x = int(pos_strings[0])
                player_y = int(pos_strings[1])
                player_z = int(pos_strings[2])
            result = player_x, player_y, player_z
        else:
            print("'"+debug_src_name+"' has bad position data--should be 3-length (x,y,z) in position value: "+str(pos_strings))
    return result

def is_same_fvec3(list_a, list_b):
    result = False
    if list_a is not None and list_b is not None:
        if len(list_a)>=3 and len(list_b)>=3:
            result = (float(list_a[0]) == float(list_b[0])) and (float(list_a[1]) == float(list_b[1])) and (float(list_a[2]) == float(list_b[2]))
    return False

def lastchar(val):
    result = None
    if (val is not None) and (len(val) > 0):
        result = val[len(val)-1]
    return result

def get_indent_string(line):
    ender_index = find_any_not(line," \t")
    result = ""
    if ender_index > -1:
        result = line[:ender_index]
    return result

def is_identifier_valid(val, is_dot_allowed):
    result = False
    these_id_chars = identifier_chars
    if is_dot_allowed:
        these_id_chars = identifier_and_dot_chars
    for index in range(0,len(val)):
        if val[index] in these_id_chars:
            result = True
        else:
            result = False
            break
    return result


#formerly get_params_len
def get_operation_chunk_len(val, start=0, step=1, line_counting_number=None):
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
    if (line_counting_number is not None) and (line_counting_number>-1):
        line_message = "line "+str(line_counting_number)+": "
    while (step > 0 and index < ender) or (step < 0 and index > ender):
        opener_number = openers.find(val[index])
        closer_number = closers.find(val[index])
        expected_closer = None
        if (len(closes)>0):
            expected_closer = lastchar(closes)
        quote_number = quotes.find(val[index])
        if (in_quote == None) and (opener_number > -1):
            opens += openers[opener_number]
            closes += closers[opener_number]
        elif (in_quote == None) and (closer_number > -1):
            if closers[closer_number] == expected_closer:
                opens = opens[:len(opens)-1]
                closes = closes[:len(closes)-1]
        elif quote_number > -1:
            if in_quote is None:
                in_quote = val[index]
            else:
                if in_quote == val[index]:
                    if (index-1 == -1) or (val[index-1]!="\\"):
                        in_quote = None
        index += step
        result += 1
        if (in_quote is None) and (len(opens)==0) and ((index>=len(val)) or (val[index] not in identifier_and_dot_chars)):
            break
    return result

def find_identifier(line, identifier_string, start=0):
    result = -1
    start_index = start
    if (identifier_string is not None) and (len(identifier_string) > 0) and (line is not None) and (len(line) > 0):
        while True:
            try_index = find_unquoted_not_commented(line, identifier_string, start=start_index)
            if (try_index > -1):
                if ((try_index==0) or (line[try_index-1] not in identifier_chars)) and ((try_index+len(identifier_string)==len(line)) or (line[try_index+len(identifier_string)] not in identifier_chars)):
                    result = try_index
                    #input(identifier_string+"starts after '"+line[try_index]+"' ends before '"+line[try_index+len(identifier_string)]+"'")
                    break
                else:
                    #match is part of a different identifier, so skip it
                    #input(identifier_string+" does not after '"+line[try_index]+"' ends before '"+line[try_index+len(identifier_string)]+"'")
                    start_index = try_index + len(identifier_string)
            else:
                break
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
    result = val.replace("\n","\\n").replace("\n","\\n")
    return result

def get_newline(file_path):
    data = None
    with open (file_path, "r") as myfile:
        data=myfile.read()
    return get_newline_in_data(data)



def is_allowed_in_variable_name_char(one_char):
    result = False
    if len(one_char) == 1:
        if one_char in identifier_chars:
            result = True
    else:
        print("error in is_allowed_in_variable_name_char: one_char must be 1 character")
    return result

def find_any_not(haystack, char_needles, start=None, step = 1):
    result = -1
    if (len(char_needles)>0) and (len(haystack)>0):
        endbefore = len(haystack)
        if start is None:
            if step > 0:
                start = 0
            elif step < 0:
                start = len(haystack)-1
        if step < 0:
            endbefore = -1
        index = start

        while (step>0 and index<endbefore) or (step<0 and index>endbefore):
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
    elements.append(haystack)  #rest of haystack is the param after last comma, else beginning if none
    return elements

#Finds needle in haystack where not quoted, taking into account escape
# sequence for single-quoted or double-quoted string inside haystack.
def find_unquoted_MAY_BE_COMMENTED(haystack, needle, start=0, endbefore=-1, step=1):
    result = -1

    prev_char = None
    if (haystack is not None) and (needle is not None) and (len(needle)>0):
        in_quote = None
        if endbefore > len(haystack):
            endbefore = len(haystack)
        if endbefore<0:
            endbefore = len(haystack)
        index = start
        if step<0:
            index = endbefore - 1
        if verbose_enable:
            print("    find_unquoted_not_commented in "+haystack.strip()+":")
        while (step>0 and index<=(endbefore-len(needle))) or (step<0 and (index>=0)):
            this_char = haystack[index:index+1]
            if verbose_enable:
                print("      {"
                    +"index:"+str(index)+";"
                    +"this_char:"+str(this_char)+";"
                    +"in_quote:"+str(in_quote)+";"
                    +"}")
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

#region formerly pcttext.py

def find_unquoted_not_commented(haystack, needle, start=0, endbefore=-1, step=1, comment_delimiter="#"):
    result = -1

    prev_char = None
    if (haystack is not None) and (needle is not None) and (len(needle)>0):
        in_quote = None
        if endbefore > len(haystack):
            endbefore = len(haystack)
        if endbefore<0:
            endbefore = len(haystack)
        index = start
        if step<0:
            index = endbefore - 1
        if verbose_enable:
            print("    find_unquoted_not_commented in "+haystack.strip()+":")
        while (step>0 and index<=(endbefore-len(needle))) or (step<0 and (index>=0)):
            this_char = haystack[index:index+1]
            if verbose_enable:
                print("      {"
                    +"index:"+str(index)+";"
                    +"this_char:"+str(this_char)+";"
                    +"in_quote:"+str(in_quote)+";"
                    +"}")
            if in_quote is None:
                if (this_char == comment_delimiter) or (haystack[index:index+3]=="\"\"\""):
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

#endregion formerly pcttext.py
