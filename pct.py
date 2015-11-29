# Author: Jake Gustafson
# Purpose: processes output from C# to Python converter at http://codeconverter.sharpdevelop.net/SnippetConverter.aspx 
# (or identical output from SharpDevelop 3.0 (Project, Tools, C# to Python))
# License: GPL
import os
import datetime
from pcttext import *
#import re  # re.escape -- why doesn't it work (printing result shows backslash then actually ends the line)


class PCTLanguageKeyword:
    
    name = None
    
    def __init__(self, name):
        self.name = name


class PCTParam:
    
    name = None
    is_required = None
    method_name = None
    class_name = None
    default_value = None
    
    def __init__(self,name,method_name,is_required=True):
        self.name = name
        self.method_name = method_name
        self.is_required = is_required

    def get_fully_qualified_name(self):
        result = self.name
        if self.method_name is not None:
            result = self.method_name + "." + result
        if self.class_name is not None:
            result = self.class_name + "." + result
        return result

class PCTMethod:

    name = None
    line_counting_number = None
    class_name = None
    
    def __init__(self, name, line_counting_number=None):
        self.name = name
        self.line_counting_number = line_counting_number

    def get_fully_qualified_name(self):
        result = self.name
        if self.class_name is not None:
            result = self.class_name + "." + result
        return result

class PCTType:
    
    name = None
    constructor_params = None
    
    def __init__(self, name, constructor_params=["value"]):
        self.name = name
        self.constructor_params = list()
        
    def get_fully_qualified_name(self):
        return self.name


class PCTSymbol:
    
    name = None
    line_counting_number = None
    including_to_line_counting_number = None
    type_identifier = None
    class_name = None
    method_name = None  #created in the scope of a method (or function) def
    default_value = None
    
    def __init__(self, name, line_counting_number, type_identifier=None, including_to_line_counting_number=None):
        self.name = name
        self.line_counting_number = line_counting_number
        self.type_identifier = type_identifier  # such as int, string, float, etc
        self.class_name = None
        self.method_name = None
        self.default_value = None
        self.including_to_line_counting_number = including_to_line_counting_number
    
    def get_fully_qualified_name(self):
        result = self.name
        if self.method_name is not None:
            result = self.method_name + "." + result
        if self.class_name is not None:
            result = self.class_name + "." + result
        return result


class PCTParser:
    
    custom_types = None
    builtin_types = None
    symbols = None  # including variables
    functions = None
    command_keywords = None
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
    unary_logical_operators = None #not
    logical_operators = None #or, and
    file_path = None
    outfile_path = None
    newline = None
    show_notices = None
    
    parser_op_preprocess = "preprocess"
    parser_op_remove_net_framework = "remove_net_framework"
    
    def print_parsing_error(self, msg):
        
        print("  (PARSING) "+msg)
        
    def print_source_error(self, msg):
        
        print("  (SOURCE) "+msg)
    
    def print_notice(self, msg):
        if self.show_notices:
            print("  (CHANGE) "+msg)
    
    def print_status(self, msg):
        
        print("  (STATUS) "+msg)
        
    def get_class_number(self, name):
        result = -1
        for index in range(0, len(self.custom_types)):
            if (self.custom_types[index] is not None) and (self.custom_types[index].name == name):
                result = index
                break
        return result

    def get_symbol_number_by_fqname(self, fqname):
        result = -1
        for index in range(0, len(self.symbols)):
            if (self.symbols[index] is not None) and (self.symbols[index].get_fully_qualified_name == fqname):
                result = index
                break
        return result

    #def get_function_number_by_fqname(self, fqname):
        #result = -1
        #for index in range(0, len(self.functions)):
            #if (self.functions[index] is not None) and (self.functions[index].get_fully_qualified_name == fqname):
                #result = index
                #break
        #return result
    
    def save_identifier_lists(self, outfile_path):
        self.print_status("save_identifier_lists...")
        self.outfile_path = outfile_path
        outfile = open(self.outfile_path, 'w')
        if self.newline is None:
            self.newline = os.sep
            self.print_parsing_error("WARNING: no file loaded, so newline '"+re_escape_visible(self.newline)+"' will be used for creating '"+outfile_path+"'.")
        indent = ""
        if self.file_path is not None:
            outfile.write(self.file_path+self.newline)
            indent += "  "
        outfile.write(indent+"custom_types:" + self.newline)
        for var in self.custom_types:
            fqname = var.get_fully_qualified_name()
            outfile.write(indent+"  " + ("  "*fqname.count(".")) + fqname + self.newline)
        outfile.write(indent+"symbols:" + self.newline)
        for var in self.symbols:
            type_prefix = ""
            if var.type_identifier is not None:
                type_prefix = var.type_identifier + " "
            fqname = var.get_fully_qualified_name()
            assignment_right_string = "  # = (no value specified)"
            if var.default_value is not None:
                assignment_right_string = " = "+var.default_value
            line_counting_number_comment = ""
            if var.line_counting_number is not None:
                line_counting_number_comment = "  # from line "+str(var.line_counting_number)
                if var.including_to_line_counting_number is not None:
                    line_counting_number_comment += " to " + str(var.including_to_line_counting_number)
            elif var.including_to_line_counting_number is not None:
                line_counting_number_comment += "#(missing starting line number) to line " + str(var.including_to_line_counting_number)
                    
            outfile.write(indent+"  " + ("  "*fqname.count(".")) + type_prefix + fqname + assignment_right_string + line_counting_number_comment + self.newline)
        outfile.write(indent+"functions:" + self.newline)
        for var in self.functions:
            fqname = var.get_fully_qualified_name()
            outfile.write(indent+"  " + ("  "*fqname.count(".")) + fqname + self.newline)
        outfile.close()
        self.print_status("OK (save_identifier_lists to '"+outfile_path+"')")
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.show_notices = False
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
        self.command_keywords = list()
        self.command_keywords.append("del")
        self.command_keywords.append("from")
        self.command_keywords.append("while")
        self.command_keywords.append("elif")
        self.command_keywords.append("global")
        self.command_keywords.append("with")
        self.command_keywords.append("assert")
        self.command_keywords.append("else")
        self.command_keywords.append("if")
        self.command_keywords.append("pass")
        self.command_keywords.append("yield")
        self.command_keywords.append("break")
        self.command_keywords.append("except")
        self.command_keywords.append("import")
        self.command_keywords.append("print")
        self.command_keywords.append("exec")
        self.command_keywords.append("raise")
        self.command_keywords.append("continue")
        self.command_keywords.append("finally")
        self.command_keywords.append("return")
        self.command_keywords.append("for")
        self.command_keywords.append("try")
        #TODO process lambda
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
        self.identity_operators.append("is not")
        self.identity_operators.append("is")
        self.operator_sets.append(self.identity_operators)
        self.membership_operators = list() #in, not in
        self.membership_operators.append("not in")
        self.membership_operators.append("in")
        self.operator_sets.append(self.membership_operators)
        self.unary_logical_operators = list()
        self.unary_logical_operators.append("not")
        self.logical_operators = list() #not, or, and
        self.logical_operators.append("or")
        self.logical_operators.append("and")
        self.operator_sets.append(self.logical_operators)
        
        self.load_file(file_path)
        
        self.process_python_lines(self.parser_op_preprocess)
        
    def load_file(self, infile_path):
        self.lines = list()
        self.data = None
        self.file_path = infile_path
        #pre-process file (get symbol names)
        infile = open(infile_path, 'r')
        while True:
            line_original = infile.readline()
            if line_original:
                line_original = line_original.strip("\n").strip("\r")
                self.lines.append(line_original)
            else:
                #no more lines in file
                break
        infile.close()
        self.print_status( str(len(self.lines)) + " line(s) detected")
        with open (infile_path, "r") as myfile:
            self.data=myfile.read()
        self.newline = None
        if self.data is not None:
            self.newline = get_newline_in_data(self.data)
        if self.newline is None:
            reason = ""
            if self.data is None:
                reason = "since data was not loaded"
            self.print_parsing_error("WARNING: could not detect newline in '"+self.file_path+"' "+reason+" so using '"+re.escape(os.sep)+"'")
            self.newline = os.sep
        else:
            self.print_status("Using '"+re_escape_visible(self.newline)+"' for newline (detected in '"+self.file_path+"').")
    #end load_file
    
    #formerly preprocess_python_framework_lines(self, infile_path)
    def process_python_lines(self, parser_op):
        participle = None
        arraylist_name = None
        arraylist_name_line_counting_number = None
        enumerator_loop_indent = None
        outfile = None
        print("")
        exn_indent = None
        exn_object_name = None
        exn_string = "traceback.format_exc()"
        exn_line_index = None
        if parser_op == self.parser_op_preprocess:
            participle = "preprocessing"
            self.classes = list()
            self.symbols = list()
            self.functions = list()
            self.custom_types = list()  # erase the custom types in case this is not the first run
        elif parser_op == self.parser_op_remove_net_framework:
            participle = "removing net framework"
            outfile = open(self.outfile_path, 'w')
        else:
            participle = "during unknown parsing operation"
            self.print_parsing_error("  ERROR in process_python_lines: unknown parsing operation '"+parser_op+"'")
        #pre-process file (get only symbol names that are always available)
        if participle is not None:
            self.print_status(""+participle+"...")
            line_index = 0
            line_counting_number = 1
            class_indent_count = None
            class_indent = None
            class_members_indent = None
            def_string = "def "
            class_name = None
            is_multiline_string = False
            multiline_delimiter = "\"\"\""
            multiline_string_name = None
            multiline_string_line_counting_number = None
            multiline_assignment_operator = None
            method_name = None
            is_method_bad = False
            method_indent = None
            if parser_op == self.parser_op_preprocess:
                is_sys_imported = False
                while line_index < len(self.lines):
                    line = self.lines[line_index]
                    line_strip = line.strip()
                    line_comment_index = find_unquoted_MAY_BE_COMMENTED(line, "#")
                    line_nocomment = line
                    if line_comment_index > -1:
                        line_nocomment = line[:line_comment_index]
                    line_nocomment_strip = line_nocomment.strip()
                    import_sys_call = "import sys"
                    #if line_strip[0:len(import_sys_call)] == import_sys_call:
                    if line_nocomment_strip == import_sys_call:
                        is_sys_imported = True
                        break
                    line_index += 1
                line_index = 0
                if not is_sys_imported:
                    #put on SECOND line to avoid messing up the BOM:
                    if (len(self.lines)>1):
                        self.lines = [self.lines[0]] + ["import sys"] + self.lines[1:]
                    else:
                        self.lines = [self.lines[0]] + ["import sys"]
            
            while line_index < len(self.lines):
                #self.print_status(""+participle+" line "+str(line_counting_number)+"...")
                line_original = self.lines[line_index]
                line = line_original
                line_strip = line.strip()
                if not is_multiline_string:
                    if line_strip[:1] != "#":
                        multiline_opener_index = line.find(multiline_delimiter)
                        inline_comment_delimiter = "#"
                        inline_comment_index = line.find(inline_comment_delimiter)
                        if (multiline_opener_index > -1) and ((inline_comment_index < 0) or (multiline_opener_index < inline_comment_index)):
                            is_multiline_string = True
                            multiline_ender_index = line.find(multiline_delimiter, multiline_opener_index+len(multiline_delimiter))
                            if multiline_ender_index > -1:
                                is_multiline_string = False
                                self.print_status("line "+str(line_counting_number)+": (source notice) triple-quoted string (or comment) ended on same line as started")
                            else:
                                multiline_string_value = line[multiline_opener_index+len(multiline_delimiter):]
                                multiline_string_name = line[:multiline_opener_index].strip()
                                multiline_string_line_counting_number = line_counting_number
                                if len(multiline_string_name) > 0:
                                    for assignment_operator in ["+=","="]:
                                        if multiline_string_name[-len(assignment_operator)] == assignment_operator:
                                            multiline_assignment_operator = assignment_operator
                                            multiline_string_name = multiline_string_name[0:-len(assignment_operator)].strip()
                                            if len(multiline_string_name) < 1:
                                                multiline_string_name = None
                                                self.print_source_error("line "+str(line_counting_number)+": (source error "+participle+") expected identifier before assignment operator (required since multiline string literal is preceeded by assignment operator)")
                                
                                else:
                                    multiline_string_name = None
                    class_opener = "class "
                    indent_count = find_any_not(line," \t")
                    indent = None
                    if (not is_multiline_string) and (line_strip[:1] != "#"):
                        if indent_count < 0:
                            indent_count = 0
                            indent = ""
                        else:
                            indent = line[0:indent_count]
                        if method_indent is not None:
                            if (len(line.strip()) > 0) and (len(indent) <= len(method_indent)):
                                method_name = None
                                method_indent = None
                                is_method_bad = False
                            #else:
                                #if method_member_indent is None:
                                    #method_member_indent = indent
                        if is_method_bad:
                            line = "#" + line
                            self.lines[line_index] = line
                            line_strip = line.strip()
                    if (not is_multiline_string) and (line_strip[:1] != "#"):
                        if (line_strip == "except , :"):
                            line = indent + "except:"
                        if (find_unquoted_not_commented(line, "except ") > -1) or (find_unquoted_not_commented(line, "except:") > -1)  or (find_unquoted_not_commented(line, "finally:") > -1):
                            next_line_indent = None
                            except_string = "except"
                            if (find_unquoted_not_commented(line, "finally:") > -1):
                                except_string = "finally"
                            next_line_number = self.find_line_nonblank_noncomment(line_index+1)
                            if next_line_number > -1:
                                next_line_indent = get_indent_string(self.lines[next_line_number])
                            #self.print_notice("line "+str(line_counting_number)+": CHECKING FOR DANGLING EXCEPTION OPENER...")
                            if (next_line_number < 0) or (len(next_line_indent) <= len(indent)):
                                one_indent = "    "
                                if line_index+1 < len(self.lines):
                                    self.lines.insert(line_index+1, indent+one_indent+"pass")
                                elif line_index+1 == len(self.lines):
                                    self.lines.append(indent+one_indent+"pass")
                                self.print_source_error("line "+str(line_counting_number)+": (WARNING: source error automatically corrected) expected indent after '"+except_string+"' so adding 'pass'")
                        
                        if exn_indent is not None:
                            if (len(line.strip()) > 0) and (len(indent) <= len(exn_indent)):
                                #the following two commented lines don't work for some reason (ignoring, using look-ahead instead)
                                #if (line_index-exn_line_index<=1):
                                #    lines.insert(line_index, exn_indent+"pass")
                                exn_indent = None
                                exn_object_name = None
                                exn_line_index = None
                        if exn_indent is not None:
                            exn_string_call = exn_object_name+".ToString()"
                            exn_string_call_index = find_unquoted_not_commented(line, exn_string_call)
                            if exn_string_call_index > -1:
                                #NOTE: do not use exn_object_name here, because was eliminated when detected on earlier line
                                fw_line = line
                                bad_string = line[exn_string_call_index:exn_string_call_index+len(exn_string_call)]
                                line = line[:exn_string_call_index] + exn_string + line[exn_string_call_index+len(exn_string_call):]
                                if fw_line != line:
                                    self.print_notice("line "+str(line_counting_number)+": (changing) using '"+exn_string+"' instead of '"+bad_string+"'")
                        else:
                            exn_opener_noname = "except:"
                            exn_opener_noname_index = find_unquoted_not_commented(line, exn_opener_noname)
                            exn_opener = "except "
                            exn_opener_index = find_unquoted_not_commented(line, exn_opener)
                            finally_opener = "finally:"
                            finally_opener_index = find_unquoted_not_commented(line, exn_opener)
                            if (exn_opener_index > -1) and (exn_opener_index == indent_count):
                                exn_line_index = line_index
                                exn_ender_index = find_unquoted_not_commented(line, ":", start=exn_opener_index+len(exn_opener))
                                exn_indent = indent
                                if exn_ender_index > -1:
                                    exn_params = explode_unquoted(line[exn_opener_index+len(exn_opener):exn_ender_index],",")
                                    exn_identifiers = list()
                                    for exn_param_original in exn_params:
                                        exn_param = exn_param_original.strip()
                                        if exn_param != "Exception":
                                            exn_identifiers.append(exn_param)
                                    if len(exn_identifiers) != 1:
                                        self.print_source_error("line "+str(line_counting_number)+": (source WARNING "+participle+") expected one exception object (got "+str(len(exn_identifiers))+": "+str(exn_identifiers)+")")
                                    if len(exn_identifiers) > 0:
                                        exn_object_name = exn_identifiers[0]
                                        self.print_status("line "+str(line_counting_number)+": detected exception object--saved name as '"+exn_object_name+"'")
                                else:
                                    self.print_source_error("line "+str(line_counting_number)+": (source error "+participle+") expected colon after exception")
                                fw_line = line
                                line = indent + "except:"
                                if fw_line != line:
                                    self.print_notice("line "+str(line_counting_number)+": (changing) using 'except' instead of '"+line_strip+"'")
                                
                            elif (exn_opener_noname_index > -1) and (exn_opener_noname_index == indent_count):
                                exn_line_index = line_index
                                #exn_ender_index = find_unquoted_not_commented(line, ":", start=exn_opener_index+len(exn_opener))
                                exn_indent = indent
                                exn_object_name = None
                                
                        if class_indent is not None:
                            if (len(line.strip()) > 0) and (len(indent) <= len(class_indent)):  # if equal, then is a global (such as variable, class, or global function)
                                self.print_status("line "+str(line_counting_number)+": -->ended class "+class_name+" (near '"+line+"')")
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
                                    if (assignment_left is not None) and (len(assignment_left) > 0) and (assignment_right is not None) and (len(assignment_right) > 0):
                                        type_string = self.get_python_first_explicit_type_id(assignment_right,line_counting_number=line_counting_number)
                                        if parser_op == self.parser_op_preprocess:
                                            #even if type_string is None (undeterminate) add it
                                            symbol = PCTSymbol(assignment_left,line_counting_number,type_identifier=type_string)
                                            symbol.class_name = class_name
                                            symbol.default_value = assignment_right
                                            self.symbols.append(symbol)
                                    else:
                                        
                                        self.print_source_error("line "+str(line_counting_number)+": (source error "+participle+") expected '"+assignment_operator+"' then value after class member")
                                #else:
                                    #class method (processed in separate case below, and parent class is added automatically if present)
                        if line_strip[:len(def_string)] == def_string:
                            method_name_opener_index = find_unquoted_not_commented(line,def_string)
                            method_name_ender_index = find_unquoted_not_commented(line, "(")
                            if method_name_opener_index > -1:
                                if method_name_ender_index > (method_name_opener_index+len(def_string)):
                                    #if method_name_ender_index>):
                                    method_name = line[method_name_opener_index+len(def_string):method_name_ender_index]
                                    method_indent = indent
                                    method_number = -1                
                                    if parser_op == self.parser_op_preprocess:
                                        if class_name is not None:
                                            method_number = self.get_function_number_using_dot_notation(class_name+"."+method_name)
                                        else:
                                            method_number = self.get_function_number_using_dot_notation(method_name)
                                        if method_number < 0:
                                            this_method = PCTMethod(method_name,line_counting_number=line_counting_number)
                                            if class_name is not None:
                                                this_method.class_name = class_name
                                            self.functions.append(this_method)
                                            method_number = len(self.functions) - 1
                                        else:
                                            is_method_bad = True
                                            line = "#" + line
                                            self.lines[line_index] = line
                                            self.print_source_error("line "+str(line_counting_number)+": source WARNING: (automatically corrected) duplicate '"+method_name+"' method starting on line--commenting since redundant (you may need to fix this by hand if this overload has code you needed).")
                                    else:
                                        method_fqname = method_name
                                        if (class_name is not None):
                                            fqname = class_name+"."+method_name
                                        method_number = self.get_function_number_using_dot_notation(fqname)
                                        if method_number < 0:
                                            self.print_parsing_error("line "+str(line_counting_number)+": (parsing error "+participle+") no method number found for method named '"+fqname+"' (was not preprocessed correctly)")
                                        #TODO: add functions to self.custom_types[class_number].children instead?
                                    if (class_name is not None) and (method_name == "__init__"):
                                        #TODO: append PCTParam objects in self.functions[method_number] to self.symbols[class_number].constructor_params
                                        pass
                                    #else:
                                    #
                                    #self.print_source_error("  source error "+participle+" line "+str(line_counting_number)+": couldn't find '(' after '"+def_string+"' and method name")
                                else:
                                    
                                    self.print_source_error("line "+str(line_counting_number)+": (source ERROR "+participle+")'"+def_string+"' should be followed by identifier then '('")
                                    
                            #else can never happen since def_string is already detected as the start of the line in the outer case
                                
                        elif line_strip[0:len(class_opener)] == class_opener:
                            if method_indent is not None:
                                
                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR "+participle+") unexpected classname in method (or function) def")
                       
                            class_indent = indent
                            class_ender = "("
                            class_ender_index = find_unquoted_not_commented(line_strip,class_ender,start=len(class_opener))
                            class_name = None
                            if class_ender_index >= 0:
                                class_name = line_strip[len(class_opener):class_ender_index].strip()
                                if len(class_name) > 0:
                                    if parser_op == self.parser_op_preprocess:
                                        pctclass = PCTType(class_name)
                                        self.custom_types.append(pctclass)
                                        class_number = len(self.custom_types) - 1
                                    else:
                                        class_number = self.get_class_number(class_name)
                                    self.print_status("line "+str(line_counting_number)+": started class "+class_name+" cache index ["+str(class_number)+"]")
                                else:
                                    
                                    self.print_source_error("line "+str(line_counting_number)+": (source ERROR "+participle+") expected classname then '"+class_ender+"' after '"+class_opener+"'")
                            else:
                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR "+participle+") expected  '"+class_ender+"' after '"+class_opener+"' and classname")
                        else:
                            #region actual processing of lines that are neither def nor class nor comment
                            inline_comment_index = find_unquoted_MAY_BE_COMMENTED(line,"#")
                            nonspace_index = find_any_not(line," \t")
                            if parser_op == self.parser_op_preprocess:
                                if method_name == "__init__":
                                    if class_name is not None:
                                        member_opener = "self."
                                        member_opener_index = find_unquoted_not_commented(line, member_opener)
                                        if member_opener_index > -1:
                                            assignment_operator = "="
                                            assignment_operator_index = find_unquoted_not_commented(line, assignment_operator, start=member_opener_index+len(member_opener))
                                            if assignment_operator_index > member_opener_index:
                                                assignment_left = line[0:assignment_operator_index].strip()
                                                assignment_right = line[assignment_operator_index+len(assignment_operator):]
                                                if inline_comment_index > -1:
                                                    assignment_right = line[assignment_operator_index+len(assignment_operator):inline_comment_index]
                                                type_id = self.get_python_first_explicit_type_id(assignment_right,line_counting_number)
                                                this_member_variable = PCTSymbol(assignment_left[len(member_opener):], line_counting_number, type_identifier=type_id)
                                                this_member_variable.class_name = class_name
                                                this_member_variable.value = assignment_right
                                                self.symbols.append(this_member_variable)
                                            else:
                                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '"+assignment_operator+"' then value after member '"+member_opener+"'")
                                    else:
                                        self.print_notice("line "+str(line_counting_number)+": (source WARNING) __init__ outside of class, so not adding any constructor-specified members")
                                elif (method_name is None) and (class_name is None):
                                    #global line
                                    #check for global variable
                                    assignment_operator = "="
                                    assignment_operator_index = find_unquoted_not_commented(line, assignment_operator)
                                    if assignment_operator_index > -1:
                                        assignment_left = line[0:assignment_operator_index].strip()
                                        assignment_right = line[assignment_operator_index+len(assignment_operator):]
                                        if assignment_left.find(".") < 0:
                                            if inline_comment_index > -1:
                                                assignment_right = line[assignment_operator_index+len(assignment_operator):inline_comment_index]
                                                type_id = self.get_python_first_explicit_type_id(assignment_right,line_counting_number)
                                                this_member_variable = PCTSymbol(assignment_left[len(member_opener):], line_counting_number, type_identifier=type_id)
                                                this_member_variable.default_value = assignment_right
                                                self.symbols.append(this_member_variable)
                                        #else:
                                            #changing value of a member of some object
                                    #else global statement but not value
                            #end if self.parser_op_preprocess
                            elif parser_op == self.parser_op_remove_net_framework:
                                import_net_framework = "from System"
                                if (line_strip[0:len(import_net_framework)+1] == import_net_framework+".") or (line_strip[0:len(import_net_framework)+1] == import_net_framework+" "):
                                    line = "#"+line
                                    self.print_notice("line "+str(line_counting_number)+": commenting useless line since imports framework")
                                else:
                                    start_index = 0
                                    while True:
                                        cts = "Convert.ToString"
                                        #print("  line "+str(line_counting_number)+","+str(start_index)+": looking for "+cts)
                                        cts_new = "str"
                                        cts_index = find_unquoted_not_commented(line, cts, start=start_index)
                                        if cts_index > -1:
                                            if (cts_index == 0) or (line[cts_index-1] not in identifier_chars):
                                                cts_ender_index = cts_index + len(cts)
                                                if (len(line)==cts_ender_index) or (line[cts_ender_index] not in identifier_chars):
                                                    line = line[:cts_index] + cts_new + line[cts_index+len(cts_new)]
                                                    start_index = cts_index + len(cts_new)
                                            else:
                                                start_index = cts_index + len(cts)
                                        else:
                                            break
                                    start_index = 0
                                    while True:
                                        fwts = "ToString"
                                        fwts_index = find_unquoted_not_commented(line, fwts, start=start_index)
                                        if fwts_index > -1:
                                            #print("  line "+str(line_counting_number)+","+str(start_index)+": processing "+fwts+" at column "+str(fwts_index+1))  # +" in '"+line+"'")
                                            dot_index = fwts_index - 1
                                            if (dot_index == 0) or (line[dot_index:dot_index+1] == "."):
                                                fwts_ender_index = fwts_index + len(fwts)
                                                if (len(line) == fwts_ender_index) or (line[fwts_ender_index] not in identifier_chars):
                                                    operand_lastchar_index = find_any_not(line, " \t", start=dot_index-1, step=-1)
                                                    if operand_lastchar_index > -1:
                                                        operand_ender_index = operand_lastchar_index + 1
                                                        operand_len = get_operation_chunk_len(line, start=operand_lastchar_index, step=-1)
                                                        operand_index = operand_ender_index-operand_len
                                                        operand = line[operand_index:operand_ender_index]
                                                        open_paren_index = find_unquoted_not_commented(line,"(",start=fwts_index+len(fwts))
                                                        if open_paren_index>-1:
                                                            fwts_params_len = get_operation_chunk_len(line, start=open_paren_index)
                                                            if (fwts_params_len>0):
                                                                fwts_params = line[open_paren_index:open_paren_index+fwts_params_len]
                                                                fw_line = line
                                                                line = line[:operand_index]+"str("+operand+")"+line[open_paren_index+fwts_params_len:]
                                                                if fwts_params!="()":
                                                                    self.print_notice("")
                                                                    self.print_notice("line "+str(line_counting_number)+": (parser WARNING) changing conversion to str("+operand+") but pushing off '.ToString' params ('"+fwts_params+"'; length "+str(fwts_params_len)+") to comment.")
                                                                    line += "  # "+fwts_params
                                                                elif fw_line != line:
                                                                    self.print_notice("line "+str(line_counting_number)+": (changing) using 'str' function instead of '.ToString'")
                                                            else:
                                                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected close parenthesis after ToString( at ["+str(fwts_index)+"]")
                                                                start_index = ftws_index + len(fwts)
                                                        else:
                                                            self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected open parenthesis after ToString( at ["+str(fwts_index)+"]")
                                                            start_index = ftws_index + len(fwts)
                                                    else:
                                                        start_index = fwts_index + len(fwts)
                                                else:
                                                    start_index = fwts_index + len(fwts)
                                            else:
                                                start_index = fwts_index + len(fwts)
                                        else:
                                            break
                                    start_index = 0
                                    while True:
                                        fwss = "Substring"
                                        #print("  line "+str(line_counting_number)+","+str(start_index)+": looking for "+fwss)
                                        fwss_index = find_unquoted_not_commented(line, fwss, start_index)
                                        if fwss_index >= 0:
                                            dot_index = fwss_index - 1
                                            if line[dot_index:dot_index+1] == ".":
                                                oparen_index = find_unquoted_not_commented(line, "(", fwss_index+len(fwss))
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
                                                            self.print_notice("line "+str(line_counting_number)+","+str(fwss_index)+": (changing) using slices instead of Substring")
                                                        else:
                                                            
                                                            self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected classname before "+fwss+" at ["+str(fwss_index)+"]")
                                                            break
                                                    else:
                                                        
                                                        self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected unquoted ')' after "+fwss+" at ["+str(fwss_index)+"]")
                                                        break
                                                else:
                                                    
                                                    self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '(' after "+fwss+" at ["+str(fwss_index)+"]")
                                                    is_mega_debug = True
                                                    oparen_index = find_unquoted_not_commented(line, "(", fwss_index+len(fwss))
                                                    is_mega_debug = False
                                                    break
                                            else:
                                                
                                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '.' before "+fwss+" at ["+str(fwss_index)+"]")
                                                break
                                        else:
                                            break
                                    #end while has Substring subscripts
                                    
                                    #TODO: should use print(x, file=sys.stderr):
                                    fw_line = line
                                    line = line.replace("Console.Error.WriteLine","sys.stderr.write")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python sys.stderr.write, write \\n, flush instead of Console.Error.WriteLine")
                                        self.lines = self.lines[:line_index+1] + [indent+"sys.stderr.write(\"\\n\")",indent+"sys.stderr.flush()"] + self.lines[line_index+1:]
                                        
                                    #TODO: should sys.stderr.write(str(x)):
                                    fw_line = line
                                    line = line.replace("Console.Error.Write","sys.stderr.write")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python sys.stderr.write instead of Console.Error.Write")
                                    fw_line = line
                                    line = line.replace("Console.Error.Flush","sys.stderr.flush")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python sys.stderr.flush instead of Console.Error.Flush")
                                    fw_line = line
                                    line = line.replace("Console.WriteLine","print")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python print instead of Console.WriteLine")
                                    #TODO: should sys.stdout.write(str(x)):
                                    fw_line = line
                                    line = line.replace("Console.Write","sys.stdout.write")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python sys.stdout.write instead of Console.Write")
                                    fw_line = line
                                    line = line.replace("Console.Out.Flush","sys.stdout.flush")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using python sys.stdout.flush instead of Console.Out.Flush")
                                    fw_line = line
                                    line = line.replace(" == None"," is None")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using ' is None' instead of ' == None'")
                                    fw_line = line
                                    line = line.replace(" != None"," is not None")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using ' is not None' instead of ' != None'")
                                    fw_line = line
                                    line = line.replace(".Replace(",".replace(")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using '.replace(' instead of '.Replace(")
                                    line = line.replace(" = ArrayList("," = list(")
                                    if fw_line != line:
                                        self.print_notice("line "+str(line_counting_number)+": (changing) using list instead of ArrayList")

                                    #NOTE: lines from multiline sections (parsed below)
                                    # must be detected in reverse order, to preserve None value when previous line is not present
                                    enumerable_name_prefix = "enumerator = "
                                    enumerable_name_suffix = ".GetEnumerator()"
                                    enumerator_loop = "while enumerator.MoveNext():"
                                    enumerator_current = " = enumerator.Current"
                                    
                                    enumerator_current_index = find_unquoted_not_commented(line,enumerator_current)
                                    if enumerator_current_index >= 0:
                                        if enumerator_loop_indent is not None:
                                            fqname = arraylist_name
                                            self_identifier_then_dot = "self."
                                            if (class_name is not None) and (fqname[:len(self_identifier_then_dot)] == self_identifier_then_dot):
                                                fqname = class_name + "." + fqname[len(self_identifier_then_dot):]
                                            #should already by fully qualified, else show error intentionally:
                                            symbol_number = self.get_symbol_number_using_dot_notation(fqname)
                                            if symbol_number < 0:
                                                theoretical_name = fqname
                                                if (class_name is not None) and (not (fqname.find(".")>-1)):
                                                    theoretical_name = class_name+"._"+arraylist_name
                                                symbol_number = self.get_symbol_number_using_dot_notation(theoretical_name)
                                                if symbol_number < 0:
                                                    
                                                    self.print_source_error("line "+str(arraylist_name_line_counting_number)+": (source ERROR) used '"+fqname+"' before declaration (tried to fix as [self a.k.a.]'"+theoretical_name+"').")
                                                    if class_name is not None:
                                                        print("    class:"+class_name)
                                                    if method_name is not None:
                                                        print("    method:"+method_name)
                                                else:
                                                    self.print_source_error("line "+str(line_counting_number)+": (WARNING, source error automatically corrected) used '"+arraylist_name+"' before declaration so automatically changed to existing '"+"self._"+fqname+"'.")
                                                    arraylist_name = "self._"+fqname
                                            line = enumerator_loop_indent + "for " + line[0:enumerator_current_index].strip() + " in " + arraylist_name + ":"
                                            arraylist_name = None
                                            enumerator_loop_indent = None
                                        else:
                                            
                                            self.print_source_error("line "+str(line_counting_number)+": (source ERROR) unexpected '"+enumerator_current+"' (since previous line is missing '"+enumerator_loop+"' or line before that is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation) {line:"+line+"}.")
                                    else:
                                        if enumerator_loop_indent is not None:
                                            
                                            self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '"+enumerator_current+"' since '"+enumerator_loop+"' was on previous line and arraylist ("+arraylist_name+") was on line before that.")
                                            

                                        enumerator_loop_index = find_unquoted_not_commented(line,enumerator_loop)
                                        if enumerator_loop_index >= 0:
                                            if arraylist_name is not None:
                                                enumerator_loop_indent = line[0:enumerator_loop_index]
                                                line = "#" + line
                                                self.print_notice("line "+str(line_counting_number)+": (changing) removing useless line '"+enumerator_loop+"' (using list iteration instead)")
                                            else:
                                                enumerator_loop_indent = None
                                                
                                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR) unexpected '"+enumerator_loop+"' (since previous line is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation).")
                                        else:
                                            enumerator_loop_indent = None
                                            if arraylist_name is not None:
                                                
                                                self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '"+enumerator_loop+"' since arraylist ("+arraylist_name+") was on previous line.")
                                                

                                            enumerable_name_prefix_index = find_unquoted_not_commented(line,enumerable_name_prefix)
                                            if enumerable_name_prefix_index >= 0:
                                                enumerable_name_suffix_index = find_unquoted_not_commented(line,enumerable_name_suffix,start=enumerable_name_prefix_index+len(enumerable_name_prefix))
                                                if enumerable_name_suffix_index >= 0:
                                                    arraylist_name = line[enumerable_name_prefix_index+len(enumerable_name_prefix):enumerable_name_suffix_index]
                                                    arraylist_name_line_counting_number = line_counting_number
                                                    self.print_status("line "+str(line_counting_number)+": detected arraylist--saved name as '"+arraylist_name+"'")
                                                else:
                                                    
                                                    self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected '"+enumerable_name_suffix+"' after '"+enumerable_name_prefix+"'")
                                                line = "#"+line
                                            else:
                                                arraylist_name = None
                                                arraylist_name_line_counting_number = None
                                    #end framework_to_standard_python (pasted from framework_to_standard_python function in etc/pctdeprecated.py)
                                #end else not import System line
                            #end if self.parser_op_remove_net_framework
                            #endregion actual processing of lines that are not def or class
                        #end else neither def nor class
                    #end if not comment (nor multiline string)
                else:
                    #continue or end multiline string
                    multiline_ender_index = line.find(multiline_delimiter)
                    if multiline_ender_index > -1:
                        is_multiline_string = False
                        if multiline_string_name is not None:
                            if parser_op == self.parser_op_preprocess:
                                multiline_string_value += line[:multiline_ender_index]
                                symbol = PCTSymbol(multiline_string_name,multiline_string_line_counting_number,type_identifier="multiline_string",including_to_line_counting_number=line_counting_number)
                                if class_name is not None:
                                    symbol.class_name = class_name
                                if method_name is not None:
                                    symbol.method_name = method_name
                                    if method_name == "__init__":
                                        symbol.default_value = multiline_string_value
                                self.symbols.append(symbol)
                            #else: #TODO: track multiline_string_value here if not preprocessing (get symbol_number using line_counting_number)
                            multiline_string_value = None
                            multiline_string_name = None
                            multiline_string_line_counting_number = None
                        else:
                            if parser_op == self.parser_op_preprocess:
                                self.print_status("line "+str(line_counting_number)+": (source notice "+participle+") treating multiline string as multiline comment")
                            
                    else:
                        multiline_string_value += line
                if outfile is not None:
                    outfile.write(line+self.newline)
                line_index += 1
                line_counting_number += 1
            #end while lines
            if is_multiline_string:
                msg = participle+": file ended before multiline string or comment"
                if multiline_string_line_counting_number is not None:
                    msg += " starting on line " + str(multiline_string_line_counting_number)
                msg += " ended"
                self.print_source_error(msg)
            if outfile is not None:
                outfile.close()
        #end if participle is not None (no valid operation detected)
    #end process_python_lines
    

    def framework_to_standard_python(self, outfile_path):
        global is_mega_debug
        self.outfile_path = outfile_path
        self.process_python_lines(self.parser_op_remove_net_framework)

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
                                        self.print_status("  found operand: "+operand)
                                    break
                                else:
                                    arithmetic_operator = None
                        if delimiter_index >= 0:
                            any_delimiter = True
                    #append last part of it (after last non-parenthetical operator or if no non-parenthetical operator)
                    assign_right_components.append(assign_right_destructable.strip())
                elif strip_assign_op_index == 0:
                    
                    self.print_source_error("line "+str(line_index+1)+": (source ERROR) unexpected assignment operator (expected identifier first) at ["+str(assign_op_index)+"] (before identifier)")
                else:
                    
                    self.print_parsing_error("line "+str(line_index+1)+": (parsing error) expected assignment operator")
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
                
    def get_python_first_explicit_type_id(self, operation_right_side_string, line_counting_number=-1):
        result = None
        operation_right_side_string = operation_right_side_string.strip()
        sign = None
        staticmethod_opener = "staticmethod("
        if operation_right_side_string[:len(staticmethod_opener)] == staticmethod_opener:
            result = "staticmethod"
        
        if result is None:
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
                    
                    line_display_string = "near '"+operation_right_side_string+"'"
                    if line_counting_number > 0:
                        line_display_string = "on line "+str(line_counting_number)
                    if sign == "-":
                        self.print_source_error("line "+str(line_counting_number)+": (source ERROR) expected only numbers or '.' after '"+sign+"'")
                    #elif other_index > 0:
                    #    #this error should only displayed if recursion was done (such as to process operators):
                    #    self.print_source_error("  source error "+str(line_counting_number)+": expected only numbers or '.' after numeric literal")
                    #else not enough information
                if (result is None) and (sign is None):
                    string_type_prefixes = ["\"","u'","u\"","b'","b\""]
                    for string_type_prefix in string_type_prefixes:
                        if operation_right_side_string[0:len(string_type_prefix)] == string_type_prefix:
                            result = "string"
                            break
            else:
                result = "int"
                
        if result is None:
            these_types = self.custom_types + self.builtin_types
            for this_type in these_types:
                this_type_name = this_type.name
                type_index = find_unquoted_not_commented(operation_right_side_string,this_type_name+"(")
                if type_index >= 0:
                    result = this_type
                    break
        return result
    #end get_python_first_explicit_type_id
    
    def get_function_number_using_dot_notation(self, fully_qualified_name):
        result = -1
        class_name = None
        method_name = fully_qualified_name
        dot_index = fully_qualified_name.find(".")
        if dot_index > 0:
            class_name = fully_qualified_name[0:dot_index]
            method_name = fully_qualified_name[dot_index+1:]
        for index in range(0,len(self.functions)):
            this_object = self.functions[index]
            if fully_qualified_name == this_object.name:
                if this_object.name.find(".") >= 0:
                    self.print_parsing_error("  ERROR: function '"+this_object.name+"' contained dot notation (parent should have been split during parsing)")
                result = index
                break
            elif (fully_qualified_name == this_object.get_fully_qualified_name()):
                result = index
                break
        return result
    
    def get_symbol_number_using_dot_notation(self, fully_qualified_name):
        result = -1
        for index in range(0,len(self.symbols)):
            this_object = self.symbols[index]
            if fully_qualified_name == this_object.name:
                if this_object.name.find(".") >= 0:
                    self.print_parsing_error("  ERROR: symbol '"+this_object.name+"' contained dot notation (parent should have been split during parsing)")
                result = index
                break
            elif (fully_qualified_name == this_object.get_fully_qualified_name()):
                result = index
                break
        return result
        
    def find_line_nonblank_noncomment(self, start_line_number=0):
        result = -1
        #is_multiline_string = False
        line_index = start_line_number
        #ml_delimiter = "\"\"\""
        while line_index < len(self.lines):
            line_original = self.lines[line_index]
            line = line_original
            line_strip = line.strip()
            line_comment_index = find_unquoted_MAY_BE_COMMENTED(line, "#")
            line_nocomment = line
            if line_comment_index > -1:
                line_nocomment = line[:line_comment_index]
            line_nocomment_strip = line_nocomment.strip()
            if len(line_nocomment_strip) > 0:
                result = line_index
                break
            line_index += 1
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
