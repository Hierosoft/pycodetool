# Author: Jake Gustafson
# Purpose: processes output from C# to Python converter at http://codeconverter.sharpdevelop.net/SnippetConverter.aspx 
# (or identical output from SharpDevelop 3.0 (Project, Tools, C# to Python))
# License: GPL
import os
import datetime
from pcttext import *
import re


class PCTLanguageKeyword:
    
    name = None
    
    def __init__(self, name):
        self.name = name


class PCTParam:
    
    name = None
    is_required = None
    
    def __init__(self,name,is_required=True):
        self.name = name
        self.is_required = is_required


class PCTType:
    
    name = None
    constructor_params = None
    
    def __init__(self, name, constructor_params=list("value")):
        self.name = name
        self.constructor_params = list()


class PCTSymbol:
    
    name = None
    line_counting_number = None
    type_identifier = None
    parent_identifier = None
    method_identifier = None  #created in the scope of a method (or function) def
    
    def __init__(self, name, line_counting_number, type_identifier=None):
        self.name = name
        self.line_counting_number = line_counting_number
        self.type_identifier = type_identifier  # such as int, string, float, etc
        self.parent_identifier = None
        self.method_identifier = None


class PCTParser:
    
    custom_types = None
    builtin_types = None
    symbols = None  # including variables
    functions = None
    keywords = None
    data = None
    
    lines = None
    operator_sets = None  #in order of operation
    arithmetic_pre_operators = None  #**
    unary_operators = None  #! + - (compliment,positive,negative)
    pre_arithmetic_operators = None  #// / * %  #in order of finding
    arithmetic_operators = None  #+ -
    bitwise_shift_operators = None #>> <<
    bitwise_pre_operators = None #&
    bitwise_operators = None #^ | (xor,or)
    comparison_operators = None #<= < > >=
    equality_operators = None #<> == !=
    assignment_operators = None # %= //= /= -= += **= *= = #in order of finding
    identity_operators = None #is, is not
    membership_operators = None #in, not in
    logical_operators = None #not, or, and
    file_path = None
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        builtin_type_strings = list()
        builtin_type_strings.append("int")
        builtin_type_strings.append("long")
        builtin_type_strings.append("float")
        builtin_type_strings.append("complex")
        builtin_type_strings.append("str")
        builtin_type_strings.append("unicode")
        builtin_type_strings.append("list")
        builtin_type_strings.append("bytearray")
        builtin_type_strings.append("buffer")
        builtin_type_strings.append("xrange")
        self.custom_types = list()
        self.builtin_types = list()
        for builtin_type_string in builtin_type_strings:
            self.builtin_types.append(PCTType(builtin_type_string))
        self.operator_sets = list()  #in order of operation
        self.arithmetic_pre_operators = list()
        self.arithmetic_pre_operators.append("**")
        self.operator_sets.append(self.arithmetic_pre_operators)
        self.unary_operators = list()  #~ + - (bitwise compliment, positive, negative)
        self.unary_operators.append("~")
        self.unary_operators.append("+")
        self.unary_operators.append("-")
        self.operator_sets.append(self.unary_operators)
        self.pre_arithmetic_operators = list()  #// / * %  #in order of finding
        self.pre_arithmetic_operators.append("//")
        self.pre_arithmetic_operators.append("/")
        self.pre_arithmetic_operators.append("*")
        self.pre_arithmetic_operators.append("%")
        self.operator_sets.append(self.pre_arithmetic_operators)
        self.arithmetic_operators = list()  #+ -
        self.arithmetic_operators.append("+")
        self.arithmetic_operators.append("-")
        self.operator_sets.append(self.arithmetic_operators)
        self.bitwise_shift_operators = list() #>> <<
        self.bitwise_shift_operators.append(">>")
        self.bitwise_shift_operators.append("<<")
        self.operator_sets.append(self.bitwise_shift_operators)
        self.bitwise_pre_operators = list() #&
        self.bitwise_pre_operators.append("&")
        self.operator_sets.append(self.bitwise_pre_operators)
        self.bitwise_operators = list() #^ | (xor,or)
        self.bitwise_operators.append("^")
        self.bitwise_operators.append("|")
        self.operator_sets.append(self.bitwise_operators)
        self.comparison_operators = list() #<= < > >=
        self.comparison_operators.append("<=")
        self.comparison_operators.append("<")
        self.comparison_operators.append(">")
        self.comparison_operators.append(">=")
        self.operator_sets.append(self.comparison_operators)
        self.equality_operators = list() #<> == !=
        self.equality_operators.append("<>")
        self.equality_operators.append("==")
        self.equality_operators.append("!=")
        self.operator_sets.append(self.equality_operators)
        self.assignment_operators = list() # %= //= /= -= += **= *= = #in order of finding
        self.assignment_operators.append("%=")
        self.assignment_operators.append("//=")
        self.assignment_operators.append("/=")
        self.assignment_operators.append("-=")
        self.assignment_operators.append("+=")
        self.assignment_operators.append("**=")
        self.assignment_operators.append("*=")
        self.assignment_operators.append("=")
        self.operator_sets.append(self.assignment_operators)
        self.identity_operators = list() #is, is not
        self.identity_operators.append("is")
        self.identity_operators.append("is not")
        self.operator_sets.append(self.identity_operators)
        self.membership_operators = list() #in, not in
        self.membership_operators.append("in")
        self.membership_operators.append("not in")
        self.operator_sets.append(self.membership_operators)
        self.logical_operators = list() #not, or, and
        self.logical_operators.append("not")
        self.logical_operators.append("or")
        self.logical_operators.append("and")
        self.operator_sets.append(self.logical_operators)
        
        load_file(file_path)
        
        self.preprocess_python_framework_lines("preprocess")
        
    def load_file(infile_path):
        self.lines = list()
        self.data = None
        self.file_path = infile_path
        #pre-process file (get symbol names)
        infile = open(infile_path, 'r')
        while True:
            line_original = infile.readline()
            if line_original:
                line_original = line_original.strip("\n")
                line_original = line_original.strip("\r")
                self.lines.append(line_original)
            else:
                #no more lines in file
                break
        infile.close()
        with open (infile_path, "r") as myfile:
            self.data=myfile.read()
    #end load_file
    
    #formerly preprocess_python_framework_lines(self, infile_path)
    def process_python_lines(self, parser_op):
        participle = "during unknown parsing operation"
        if parser_op = "preprocess":
            self.classes = list()
            self.symbols = list()
            self.functions = list()
            self.lines = list()
            self.custom_types = list()  # erase the custom types in case this is not the first run
            participle = "preprocessing"
        
        #pre-process file (get only symbol names that are always available)
        line_index = 0
        line_counting_number = 1
        class_indent_count = None
        class_indent = None
        class_members_indent = None
        is_multiline_string = False
        multiline_delimiter = "\"\"\""
        def_string = "def "
        class_name = None
        multiline_string_name = None
        method_name = None
        method_indent = None
        while line_index < len(self.lines):
            line_original = self.lines[line_index]
            line_original = line_original.strip("\r").strip("\n")
            line = line_original
            line_strip = line.strip()
            if not is_multiline_string:
                if line_strip[:1] != "#":
                    multiline_opener_index = line.find(multiline_delimiter)
                    inline_comment_delimiter = "#"
                    inline_comment_index = find_unquoted_MAY_BE_COMMENTED(line, inline_comment_delimiter)
                    if (multiline_comment_index > -1) and (multiline_comment_index < inline_comment_index):
                        is_multiline_string = True
                        multiline_ender_index = find_unquoted_MAY_BE_COMMENTED(line, multiline_delimiter, start = multiline_opener_index+len(multiline_delimiter))
                        if multiline_ender_index > -1:
                            is_multiline_string = False
                        else:
                            multiline_string_value = line[inline_comment_index+len(inline_comment_delimiter):]
                if (not is_multiline_string) and (line_strip[:1] != "#"):
                    class_opener = "class "
                    indent_count = find_any_not(line," \t")
                    indent = None
                    if indent_count < 0:
                        indent_count = 0
                        indent = ""
                    else:
                        indent = line[0:indent_count]
                    if method_indent is not None:
                        if len(indent) <= len(method_indent):
                            method_name = None
                            method_indent = None
                        #else:
                            #if method_member_indent is None:
                                #method_member_indent = indent
                    
                    if class_indent is not None:
                        if len(indent) <= len(class_indent):  # if equal, then is a global (such as variable, class, or global function)
                            class_indent = None
                            class_members_indent = None
                            class_name = None
                            class_number = None
                    if class_indent is not None:
                        if class_members_indent is None:
                            if len(line_strip) > 0:
                                class_members_indent = indent
                        if indent == class_members_indent:
                            if line_strip[0:len(def_string)] != def_string:
                                assignment_operator = "="
                                assignment_operator_index = find_unquoted_not_commented(line, assignment_operator)
                                assignment_left = None
                                assignment_right = None
                                if assignment_operator_index > -1:
                                    assignment_left = line[0:assignment_operator_index].strip()
                                    assignment_right = line[assignment_operator_index+len(assignment_operator):]
                                if (len(assignment_left) > 0) and (len(assignment_right) > 0):
                                    type_string = self.python_detect_first_explicit_type_id(assignment_right,line_counting_number=line_counting_number)
                                    if parser_op = "preprocess":
                                        #even if type_string is None (undeterminate) add it
                                        symbol = PCTSymbol(assignment_left,line_counting_number,type_identifier=type_string)
                                        symbol.parent_identifier = class_name
                                        self.symbols.append(symbol)
                                else:
                                    print("")
                                    print("  script error "+participle+" line "+str(line_counting_number)+": expected '"+assignment_operator+"' then value after class member")
                            else:
                                #class method
                                method_name_opener_index = find_unquoted_not_commented(line,def_string)
                                method_name_ender_index = find_unquoted_not_commented(line, "(")
                                if method_name_opener_index > -1:
                                    if method_name_ender_index > -1:
                                        if method_name_ender_index>(method_name_opener_index+len(def_string)):
                                            method_name = line[method_name_opener_index:method_name_ender_index]
                                            method_indent = indent
                                            if method_name = "__init__"
                                                pass
                                                #TODO: append PCTParam objects to self.symbols[class_number].constructor_params
                                        else:
                                            print("")
                                            print("  script error "+participle+" line "+str(line_counting_number)+": couldn't find '(' after '"+def_string+"' and method name")
                    
                                    if parser_op = "preprocess":
                                        if method_name is not None:
                                            self.functions.append(this_method)
                                else:
                                    else:
                        if line_strip[:len(def_string)] == def_string:
                            method_indent = indent
                            method_name = name
                            if parser_op = "preprocess":
                                if method_name is not None:
                                    self.functions.append(this_method)
                            
                    if line_strip[0:len(class_opener)] == class_opener:
                        if method_indent is not None:
                            print("")
                            print("  script error "+participle+" line "+str(line_counting_number)+": unexpected classname in method (or function) def")
                   
                        class_indent = indent
                        class_ender = "("
                        class_ender_index = find_unquoted_not_commented(line_strip,class_ender,start=len(class_opener))
                        class_name = None
                        if class_ender_index >= 0:
                            class_name = line_strip[len(class_opener):class_ender_index].strip()
                        if len(class_name) > 0:
                            pctclass = PCTType(class_name)
                            self.custom_types.append(pctclass)
                            class_number = len(self.custom_types) - 1
                        else:
                            print("")
                            print("  script error "+participle+" line "+str(line_counting_number)+": expected classname then '"+class_ender+"' after '"+class_opener+"'")
                    #elif
                #end if not comment (nor multiline string)
            else:
                #continue or end multiline string
                multiline_ender_index = find_unquoted_MAY_BE_COMMENTED(line, multiline_delimiter)
                if multiline_ender_index > -1:
                    is_multiline_string = False
                    if multiline_string_name is not None:
                        if parsing_op = "preprocess":
                            multiline_string_value += line[:multiline_ender_index]
                            symbol = PCTSymbol(multiline_string_name,line_counting_number,type_identifier=type_string)
                            if class_name is not None:
                                symbol.parent_identifier = class_name
                            if method_name is not None:
                                symbol.method_identifier = method_name
                            self.symbols.append(symbol)
                        #else: #TODO: track multiline_string_value here if not preprocessing (get symbol_number using line_counting_number)
                        multiline_string_value = None
                    else:
                        print("  (NOTICE) "+participle+" line "+str(line_counting_number)+": treating multiline string as multiline comment")
                else:
                    multiline_string_value += line
            line_index += 1
            line_counting_number += 1
    #end preprocess_python_framework_lines
    
    #first index returns how many lines are in the assignment
    # (only works for triple-double quote syntax so far) and
    # formerly called: 
    #def split_assignment_line(index, assignment_operator_list):
    def collect_python_identifiers(self, index, assignment_operator_list):
        result = None
        if index<len(lines):
            line = lines[index]
            #assign_op = " = "
            #assign_op_index = self.find_unquoted_not_commented(assign_op)
            assign_op = None
            assign_op_index = -1
            for i in range(0,len(assignment_operator_list)):
                assign_op = assignment_operator_list[i]
                assign_op_index = find_unquoted_not_commented_not_parenthetical(line,assign_op)
                if assign_op_index >= 0:
                    break
                else:
                    assign_op = None
            if assign_op_index >= 0:
                result = list()
                strip_assign_op_index = -1
                if assign_op is not None:
                    strip_assign_op_index = find_unquoted_not_commented(line.strip(),assign_op)
                if strip_assign_op_index > 0:
                    assign_left = line[0:assign_op_index].strip()
                    assign_right = line[assign_op_index+len(assign_op):].strip()
                    assign_right_destructable = assign_right
                    assign_right_components = list()
                    any_delimiter = True
                    while any_delimiter:
                        any_delimiter = False
                        delimiter_index = -1
                        arithmetic_operator = None
                        for operator_set_number in range(0,len(self.operator_sets)):
                            operator_list = self.operator_sets[operator_set_number]
                            for operator_number in range(0,len(operator_list)):
                                operator = operator_list[operator_number]
                                operator_index = find_unquoted_not_commented(assign_right_destructable, operator)
                                if delimiter_index >= 0:
                                    operand = assign_right_destructable[0:operator_index].strip()
                                    assign_right_destructable = assign_right_destructable[operator_index+len(operator):]
                                    if len(operand)>0:
                                        assign_right_components.append(operand)
                                        print("        found operand: "+operand)
                                    break
                                else:
                                    arithmetic_operator = None
                        if delimiter_index >= 0:
                            any_delimiter = True
                    #append last part of it (after last non-parenthetical operator or if no non-parenthetical operator)
                    assign_right_components.append(assign_right_destructable.strip())
                elif strip_assign_op_index == 0:
                    print("")
                    print("  script error on line "+str(line_index+1)+": unexpected assignment operator (expected identifier first) at ["+str(assign_op_index)+"] (before identifier)")
                else:
                    print("")
                    print("  parsing error on line "+str(line_index+1)+": expected assignment operator")
        return result
    #end collect_python_identifiers
    
    #def get_type_identifier_recursively(line):
    #    result = None
    #    line_index = 0
    #    line_counting_number = 1
    #    while line_index < len(self.lines):
    #        line_original = self.lines[line_index]
    #        line = line_original
    #        
    #        line_index += 1
    #        line_counting_number += 1
    #    return result
            
    def framework_to_standard_python(self, outfile_path):
        global is_mega_debug
        newline = None
        if self.data is not None:
            newline = get_newline_in_data(self.data)
        if newline is None:
            reason = ""
            if self.data is None:
                reason = "since data was not loaded"
            print("WARNING: could not detect newline in '"+self.file_path+"' "+reason+" so using '"+re.escape(os.sep)+"'")
            newline = os.sep
        else:
            print("NOTICE: Detected newline '"+re.escape(newline)+"' in '"+self.file_path+"'.")
        outfile = open(outfile_path, 'w')
        line_index = 0
        line_counting_number = 1
        arraylist_name = None
        enumerator_loop_indent = None
        
        #post-process file:
        while line_index < len(self.lines):
            line_original = self.lines[line_index]
            line_original = line_original.strip("\n").strip("\r")
            line = line_original
            line_strip = line.strip()
            if line_strip[:1] != "#":
                #while "Substring" in line:
                key = "from System"
                if line_strip[0:len(key)] == key:
                    line = "#"+line
                    print("commenting useless line "+str(line_counting_number)+" since imports framework")
                else:
                    while True:
                        key = "Substring"
                        key_index = find_unquoted_not_commented(line, key)
                        if key_index >= 0:
                            dot_index = key_index - 1
                            if line[dot_index:dot_index+1] == ".":
                                oparen_index = find_unquoted_not_commented(line, "(", key_index+len(key))
                                if oparen_index >= 0:
                                    cparen_index = find_unquoted_not_commented(line, ")", oparen_index+1)
                                    if cparen_index >= 0:
                                        params = explode_unquoted(line[oparen_index+1:cparen_index], ",")
                                        parent_start_after_index = find_any_not(line[0:dot_index], identifier_chars, step=-1)
                                        if parent_start_after_index >= -1:
                                            parent_index = parent_start_after_index + 1
                                            parent_string = line[parent_start_after_index:dot_index]
                                            if (len(params)>1):
                                                line = line[0:parent_index]+parent_string+"["+params[0]+":"+params[0]+"+"+params[1]+"]"
                                            else:
                                                line = line[0:parent_index]+parent_string+"["+params[0]+":]"
                                            print("  changing line "+str(line_counting_number)+","+str(key_index)+": using slices instead of Substring")
                                        else:
                                            print("")
                                            print("  script error on line "+str(line_counting_number)+": expected classname before "+key+" at ["+str(key_index)+"]")
                                            break
                                    else:
                                        print("")
                                        print("  script error on line "+str(line_counting_number)+": expected unquoted ')' after "+key+" at ["+str(key_index)+"]")
                                        break
                                else:
                                    print("")
                                    print("  script error on line "+str(line_counting_number)+": expected '(' after "+key+" at ["+str(key_index)+"]")
                                    is_mega_debug = True
                                    oparen_index = find_unquoted_not_commented(line, "(", key_index+len(key))
                                    is_mega_debug = False
                                    break
                            else:
                                print("")
                                print("  script error on line "+str(line_counting_number)+": expected '.' before "+key+" at ["+str(key_index)+"]")
                                break
                        else:
                            break
                    #end while has Substring subscripts
                    line_prev = line
                    line = line.replace("Console.Error.WriteLine","print")
                    if line_prev != line:
                        print("changing line "+str(line_counting_number)+": using python print instead of Console.Error.WriteLine")
                    line_prev = line
                    line = line.replace("Console.Error.Write","print")
                    if line_prev != line:
                        print("changing line "+str(line_counting_number)+": using python print instead of Console.Error.Write")
                    line_prev = line
                    line = line.replace(" == None"," is None")
                    if line_prev != line:
                        print("changing line "+str(line_counting_number)+": using ' is None' instead of ' == None'")
                    line_prev = line
                    line = line.replace(" != None"," is not None")
                    if line_prev != line:
                        print("changing line "+str(line_counting_number)+": using ' is not None' instead of ' != None'")
                    line_prev = line
                    line = line.replace(".Replace(",".replace(")
                    if line_prev != line:
                        print("changing line "+str(line_counting_number)+": using '.replace(' instead of '.Replace(")

                    #NOTE: lines from multiline sections (parsed below) must be detected in reverse order to preserve None value when previous line is not present
                    enumerable_name_prefix = "enumerator = "
                    enumerable_name_suffix = ".GetEnumerator()"
                    enumerator_loop = "while enumerator.MoveNext():"
                    enumerator_current = " = enumerator.Current"
                    
                    enumerator_current_index = find_unquoted_not_commented(line,enumerator_current)
                    if enumerator_current_index >= 0:
                        if enumerator_loop_indent is not None:
                            fqname = arraylist_name
                            #should already by fully qualified, else show error intentionally:
                            symbol_number = self.get_symbol_number_using_dot_notation(fqname)
                            if symbol_number < 0:
                                theoretical_name = class_name+"._"+fqname
                                symbol_number = self.get_symbol_number_using_dot_notation(theoretical_name)
                                if symbol_number < 0:
                                    print("")
                                    print("  script error on line "+str(line_counting_number)+": used '"+fqdn+"' before declaration.")
                                else:
                                    print("")
                                    print("  WARNING: (automatically corrected) script error on line "+str(line_counting_number)+": used '"+arraylist_name+"' where only '"+"self._"+fqname+"' exists.")
                                    arraylist_name = "self._"+fqname
                            line = enumerator_loop_indent + "for " + line[0:enumerator_current_index].strip() + " in " + arraylist_name + ":"
                            arraylist_name = None
                            enumerator_loop_indent = None
                        else:
                            print("")
                            print("  script error on line "+str(line_counting_number)+": unexpected '"+enumerator_current+"' (since previous line is missing '"+enumerator_loop+"' or line before that is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation) {line:"+line+"}.")
                    else:
                        if enumerator_loop_indent is not None:
                            print("")
                            print("  script error on line "+str(line_counting_number)+": expected '"+enumerator_current+"' since '"+enumerator_loop+"' was on previous line and arraylist ("+arraylist_name+") was on line before that.")
                            

                        enumerator_loop_index = find_unquoted_not_commented(line,enumerator_loop)
                        if enumerator_loop_index >= 0:
                            if arraylist_name is not None:
                                enumerator_loop_indent = line[0:enumerator_loop_index]
                                line = "#" + line
                                print("  "+"removing useless line '"+enumerator_loop+"' (using list iteration instead)")
                            else:
                                enumerator_loop_indent = None
                                print("")
                                print("  script error on line "+str(line_counting_number)+": unexpected '"+enumerator_loop+"' (since previous line is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation).")
                        else:
                            enumerator_loop_indent = None
                            if arraylist_name is not None:
                                print("")
                                print("  script error on line "+str(line_counting_number)+": expected '"+enumerator_loop+"' since arraylist ("+arraylist_name+") was on previous line.")
                                

                            enumerable_name_prefix_index = find_unquoted_not_commented(line,enumerable_name_prefix)
                            if enumerable_name_prefix_index >= 0:
                                enumerable_name_suffix_index = find_unquoted_not_commented(line,enumerable_name_suffix,start=enumerable_name_prefix_index+len(enumerable_name_prefix))
                                if enumerable_name_suffix_index >= 0:
                                    arraylist_name = line[enumerable_name_prefix_index+len(enumerable_name_prefix):enumerable_name_suffix_index]
                                    print("detected arraylist on line "+str(line_counting_number)+": saved name as '"+arraylist_name+"'")
                                else:
                                    print("")
                                    print("  script error on line "+str(line_counting_number)+": expected '"+enumerable_name_suffix+"' after '"+enumerable_name_prefix+"'")
                                line = "#"+line
                            else:
                                arraylist_name = None
                    
            outfile.write(line+newline)
            line_index += 1
            line_counting_number += 1
        
        outfile.close()
    #end framework_to_standard_python
    
    def python_detect_first_explicit_type_id(self, operation_right_side_string, line_counting_number=-1):
        result = None
        operation_right_side_string = operation_right_side_string.strip()
        sign = None
        number_string = operation_right_side_string
        if operation_right_side_string[0:1] == "-":
            number_string = operation_right_side_string[1:]
            sign = "-"
        other_index = find_any_not(number_string, digit_chars)
        delimiter = None
        whole_number_string = number_string
        decimal_string = None
        if other_index >= 0:
            other = number_string[other_index:other_index+1]
            if other == ".":
                whole_number_string = number_string[0:other_index]
                decimal_string = number_string[other_index+1:]
                junk_index = find_any_not(decimal_string, digit_chars)
                if junk_index < 0:
                    result = "decimal"
                #TODO: make this recursive here (process operator at junk_index and all others)
            else:
                print("")
                line_display_string = "near '"+operation_right_side_string+"'"
                if line_counting_number > 0:
                    line_display_string = "on line "+str(line_counting_number)
                if sign == "-":
                    print("  script error "+str(line_counting_number)+": expected only numbers or '.' after '"+sign+"'")
                #elif other_index > 0:
                #    #this error should only displayed if recursion was done (such as to process operators):
                #    print("  script error "+str(line_counting_number)+": expected only numbers or '.' after numeric literal")
                #else not enough information
            if (result is None) and (sign is None):
                string_type_prefixes = list("\"","u'","u\"","b'","b\"")
                for string_type_prefix in string_type_prefixes:
                    if operation_right_side_string[0:len(string_type_prefix)] == string_type_prefix:
                        result = "string"
                        break
        else:
            result = "int"
                
        if result is None:
            these_types = self.custom_types + self.builtin_types
            for this_type in these_types:
                type_index = find_unquoted_not_commented(operation_right_side_string,this_type+"(")
                if type_index >= 0:
                    result = this_type
                    break
        return result
    #end python_detect_first_explicit_type_id
    
    
    def get_symbol_number_using_dot_notation(self, symbol_fully_qualified_name):
        result = -1
        for symbol_index in range(0,len(self.symbols)):
            symbol = self.symbols(symbol_index)
            if symbol_fully_qualified_name == symbol.name:
                if symbol.name.find(".") >= 0:
                    print("  ERROR: symbol '"+symbol.name+"' contained dot notation (parent should have been split during parsing)")
                result = symbol_index
                break
            elif (symbol.parent_identifier is not None) and (symbol_fully_qualified_name == symbol.parent_identifier+"."+symbol.name):
                result = symbol_index
                break
        return result
    
    #def get_parsed_symbol_by_id(sid):
        #result = None
        #return result
    
    #def name_psid(name):
        #result = None
        #prefix = "class["
        #suffix = "]"
        #for index in range(0,len(classes)):
            #if classes[index].name==name:
                #result = prefix+str(index)+suffix
                #break
        
        #return result
    
    #def split_assignments_intial_only(index):
    #    assignment_operator_list = list()
    #    assignment_operator_list.append(" = ")
    #    return split_assignment_line(index, assignment_operator_list)
    
    
    #def split_assignment_line_any_assignment_method(index):
    #    assignment_operator_list = list()
    #    assignment_operator_list += self.comparison_operators + self.equality_operators + self.assignment_operators
    #    return split_assignment_line(index, assignment_operator_list)
