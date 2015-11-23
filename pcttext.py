

uppercase_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
lowercase_chars = uppercase_chars.lower()
letter_chars = uppercase_chars+lowercase_chars
digit_chars = "0123456789"
identifier_chars = letter_chars+"_"+digit_chars

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

def find_any_not(haystack, char_needles, step = 1):
    result = -1
    if (len(char_needles)>0) and (len(haystack)>0):
        endbefore = len(haystack)
        start = 0
        if step < 0:
            start = len(haystack)-1
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
