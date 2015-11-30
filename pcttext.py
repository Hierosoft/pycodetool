

uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lowercase_chars = uppercase_chars.lower()
letter_chars = uppercase_chars+lowercase_chars
digit_chars = "0123456789"
identifier_chars = letter_chars+"_"+digit_chars
identifier_and_dot_chars = identifier_chars + "."

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

is_mega_debug = False
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
        if is_mega_debug:
            print("    find_unquoted_not_commented in "+haystack.strip()+":")
        while (step>0 and index<=(endbefore-len(needle))) or (step<0 and (index>=0)):
            this_char = haystack[index:index+1]
            if is_mega_debug:
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
    
def find_unquoted_not_commented(haystack, needle, start=0, endbefore=-1, step=1):
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
        if is_mega_debug:
            print("    find_unquoted_not_commented in "+haystack.strip()+":")
        while (step>0 and index<=(endbefore-len(needle))) or (step<0 and (index>=0)):
            this_char = haystack[index:index+1]
            if is_mega_debug:
                print("      {"
                    +"index:"+str(index)+";"
                    +"this_char:"+str(this_char)+";"
                    +"in_quote:"+str(in_quote)+";"
                    +"}")
            if in_quote is None:
                if (this_char == "#") or (haystack[index:index+3]=="\"\"\""):
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
