# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Author: Jake Gustafson
Purpose: processes output from C# to Python converter at
http://codeconverter.sharpdevelop.net/SnippetConverter.aspx
(or identical output from SharpDevelop 3.0 (Project, Tools, C# to
Python))
License: GPL 2 or later
"""
import os
# import datetime
import time
from pycodetool.parsing import (
    find_unquoted_not_commented,
    find_unquoted_even_commented,
    find_any_not,
    find_identifier,
    find_unquoted_not_commented_not_parenthetical,
    identifier_chars,
    is_identifier_valid,
    digit_chars,
    explode_unquoted,
)
# import re  # re.escape
# ^ why doesn't it work (printing result shows backslash then actually
# ends the line)

convert_note = ("# Processed by pycodetool"
                " https://github.com/poikilos/pycodetool")


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

    def __init__(self, name, method_name, is_required=True):
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
    lineN = None
    class_name = None

    def __init__(self, name, lineN=None):
        self.name = name
        self.lineN = lineN

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
    """
    Represent a code symbol. This is a class for parsing code.

    members:
    method_name -- It is not None only if the variable was declared in
                   the scope of a method (or function) definition.
    """
    name = None
    lineN = None
    itlN = None  # including_to_line_counting_number
    type_identifier = None
    class_name = None
    method_name = None
    default_value = None

    def __init__(self, name, lineN, type_identifier=None, itlN=None):
        """
        Keyword arguments:
        type_identifier -- such as int, string, float, etc
        itlN -- including_to_line_counting_number
        """
        self.name = name
        self.lineN = lineN
        self.type_identifier = type_identifier
        self.class_name = None
        self.method_name = None
        self.default_value = None
        self.itlN = itlN

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
    # data = None

    lines = None
    operator_sets = None  # in order of operation
    arithmetic_pre_operators = None  # **
    unary_operators = None  # ! + - (compliment,positive,negative)
    pre_arithmetic_operators = None  # // / * %  #in order of finding
    arithmetic_operators = None  # + -
    bitwise_shift_operators = None  # >> <<
    bitwise_pre_operators = None  # &
    bitwise_operators = None  # ^ | (xor,or)
    comparison_operators = None  # <= < > >=
    equality_operators = None  # <> == !=
    assignment_operators = None
    # ^ %= //= /= -= += **= *= = #in order of finding
    identity_operators = None  # s, is not
    membership_operators = None  # in, not in
    unary_logical_operators = None  # not
    logical_operators = None  # or, and
    file_path = None
    outfile_path = None
    newline = None
    show_notices = None
    sw_object_strings = None
    extra_lines_cumulative = None
    parser_op_preprocess = "preprocess"
    parser_op_remove_net_framework = "remove_net_framework"

    def pperr(self, msg):
        """print_parsing_error"""
        print("  (PARSING) "+msg)

    def pserr(self, msg):
        """print_source_error"""
        print("  (SOURCE) "+msg)

    def pinfo(self, msg):
        """print_notice"""
        if self.show_notices:
            print("  (CHANGE) "+msg)

    def pstat(self, msg):
        """print_status"""
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

    # def get_function_number_by_fqname(self, fqname):
    #     result = -1
    #     for index in range(0, len(self.functions)):
    #         if (self.functions[index] is not None) and (self.functions[index].get_fully_qualified_name == fqname):
    #             result = index
    #             break
    #     return result

    def save_identifier_lists(self, outfile_path):
        self.pstat("save_identifier_lists...")
        self.outfile_path = outfile_path
        outfile = open(self.outfile_path, 'w')
        if self.newline is None:
            self.newline = "\n"  # NOTE: python automatically changes instances of \n to os.sep, so would change os.sep to \r\r\n so don't use os.sep
            # self.newline = os.sep
            # self.pperr("WARNING: no file loaded, so newline '"+re_escape_visible(self.newline)+"' will be used for creating '"+outfile_path+"'.")
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
            if var.lineN is not None:
                line_counting_number_comment = "  # from line "+str(var.lineN)
                if var.itlN is not None:
                    line_counting_number_comment += " to " + str(var.itlN)
            elif var.itlN is not None:
                line_counting_number_comment += "#(missing starting line number) to line " + str(var.itlN)

            outfile.write(indent+"  " + ("  "*fqname.count(".")) + type_prefix + fqname + assignment_right_string + line_counting_number_comment + self.newline)
        outfile.write(indent+"functions:" + self.newline)
        for var in self.functions:
            fqname = var.get_fully_qualified_name()
            outfile.write(indent+"  " + ("  "*fqname.count(".")) + fqname + self.newline)
        outfile.close()
        self.pstat("OK (save_identifier_lists to '"+outfile_path+"')")

    def __init__(self, file_path):
        self.file_path = file_path
        # self.data = None
        self.show_notices = True
        self.sw_object_strings = list()
        self.extra_lines_cumulative = 0
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
        # TODO process lambda
        self.custom_types = list()
        self.builtin_types = list()
        for builtin_type_string in builtin_type_strings:
            self.builtin_types.append(PCTType(builtin_type_string))
        self.operator_sets = list()  # in order of operation
        self.arithmetic_pre_operators = list()
        self.arithmetic_pre_operators.append("**")
        self.operator_sets.append(self.arithmetic_pre_operators)
        self.unary_operators = list()  # ~ + - (bitwise compliment,
        #                              # positive, negative)
        self.unary_operators.append("~")
        self.unary_operators.append("+")
        self.unary_operators.append("-")
        self.operator_sets.append(self.unary_operators)
        self.pre_arithmetic_operators = list()  # // / * %  #in order of
        #                                       # finding
        self.pre_arithmetic_operators.append("//")
        self.pre_arithmetic_operators.append("/")
        self.pre_arithmetic_operators.append("*")
        self.pre_arithmetic_operators.append("%")
        self.operator_sets.append(self.pre_arithmetic_operators)
        self.arithmetic_operators = list()  # + -
        self.arithmetic_operators.append("+")
        self.arithmetic_operators.append("-")
        self.operator_sets.append(self.arithmetic_operators)
        self.bitwise_shift_operators = list()  # >> <<
        self.bitwise_shift_operators.append(">>")
        self.bitwise_shift_operators.append("<<")
        self.operator_sets.append(self.bitwise_shift_operators)
        self.bitwise_pre_operators = list()  # &
        self.bitwise_pre_operators.append("&")
        self.operator_sets.append(self.bitwise_pre_operators)
        self.bitwise_operators = list()  # ^ | (xor,or)
        self.bitwise_operators.append("^")
        self.bitwise_operators.append("|")
        self.operator_sets.append(self.bitwise_operators)
        self.comparison_operators = list()  # <= < > >=
        self.comparison_operators.append("<=")
        self.comparison_operators.append("<")
        self.comparison_operators.append(">")
        self.comparison_operators.append(">=")
        self.operator_sets.append(self.comparison_operators)
        self.equality_operators = list()  # <> == !=
        self.equality_operators.append("<>")
        self.equality_operators.append("==")
        self.equality_operators.append("!=")
        self.operator_sets.append(self.equality_operators)
        self.assignment_operators = list()  # %= //= /= -= += **= *= =
        #                                   # in order of finding
        self.assignment_operators.append("%=")
        self.assignment_operators.append("//=")
        self.assignment_operators.append("/=")
        self.assignment_operators.append("-=")
        self.assignment_operators.append("+=")
        self.assignment_operators.append("**=")
        self.assignment_operators.append("*=")
        self.assignment_operators.append("=")
        self.operator_sets.append(self.assignment_operators)
        self.identity_operators = list()  # is, is not
        self.identity_operators.append("is not")
        self.identity_operators.append("is")
        self.operator_sets.append(self.identity_operators)
        self.membership_operators = list()  # in, not in
        self.membership_operators.append("not in")
        self.membership_operators.append("in")
        self.operator_sets.append(self.membership_operators)
        self.unary_logical_operators = list()
        self.unary_logical_operators.append("not")
        self.logical_operators = list()  # not, or, and
        self.logical_operators.append("or")
        self.logical_operators.append("and")
        self.operator_sets.append(self.logical_operators)

        self.load_file(file_path)

        self.process_python_lines(self.parser_op_preprocess)

    def load_file(self, infile_path):
        self.lines = list()
        # self.data = None
        self.file_path = infile_path
        # pre-process file (get symbol names)
        infile = open(infile_path, 'r')
        while True:
            line_original = infile.readline()
            if line_original:
                line_original = line_original.strip("\n").strip("\r")
                self.lines.append(line_original)
            else:
                # no more lines in file
                break
        infile.close()
        self.pstat(str(len(self.lines)) + " line(s) detected")
        # with open (infile_path, "r") as myfile:
        #     self.data=myfile.read()
        self.newline = "\n"
        # ^ python automatically changes instances of \n to os.sep, so
        # would change os.sep to \r\r\n so don't use os.sep
        # self.newline = None
        # if self.data is not None:
        #     self.newline = get_newline_in_data(self.data)
        # if self.newline is None:
        #     reason = ""
        #     if self.data is None:
        #         reason = "since data was not loaded"
        #     self.pperr("WARNING: could not detect newline in '"
        #                + self.file_path + "' " + reason + " so using '"
        #                + re.escape(os.sep) + "'")
        #     self.newline = os.sep
        # else:
        #     self.pstat("Using '" + re_escape_visible(self.newline)
        #                + "' for newline (detected in '"
        #                + self.file_path + "').")
    # end load_file

    # formerly preprocess_python_framework_lines(self, infile_path)
    def process_python_lines(self, parser_op):
        fUNC = find_unquoted_not_commented
        participle = None
        arraylist_name = None
        alNameN = None  # arraylist_name_line_counting_number
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
            self.custom_types = list()  # erase the custom types in
            #                           # case this is not the first run
        elif parser_op == self.parser_op_remove_net_framework:
            participle = "removing net framework"
            outfile = open(self.outfile_path, 'w')
        else:
            participle = "during unknown parsing operation"
            self.pperr("  ERROR in process_python_lines:"
                       " unknown parsing operation '" + parser_op + "'")
        # pre-process file
        # (get only symbol names that are always available)
        if participle is not None:
            self.pstat(""+participle+"...")
            line_index = 0
            lineN = 1
            class_indent_count = None
            class_indent = None
            class_members_indent = None
            def_string = "def "
            class_name = None
            is_multiline_string = False
            mlD = "\"\"\""  # multiline_delimiter
            mlsName = None
            mlsN = None  # multiline_string_line_counting_number
            mlao = None  # multiline_assignment_operator
            method_name = None
            is_method_bad = False
            method_indent = None
            extra_lines = 0

            extra_lines_passed = 0
            if parser_op == self.parser_op_preprocess:
                self.extra_lines_cumulative = 0
                is_sys_imported = False
                is_convert_note_prepended = False
                convert_note_dated = (
                    convert_note + " "
                    + time.strftime("%Y-%m-%d %H:%M:%S")
                )
                while line_index < len(self.lines):
                    line = self.lines[line_index]
                    line_strip = line.strip()
                    line_comment_index = find_unquoted_even_commented(
                        line,
                        "#"
                    )
                    line_nocomment = line
                    if line_comment_index > -1:
                        line_nocomment = line[:line_comment_index]
                    line_nocomment_strip = line_nocomment.strip()
                    import_sys_call = "import sys"
                    # if line_strip[0:len(import_sys_call)] == import_sys_call:
                    if line_nocomment_strip == import_sys_call:
                        is_sys_imported = True
                        break
                    convert_note_index = line.find(convert_note)
                    if convert_note_index > -1:
                        is_convert_note_prepended = True
                    line_index += 1
                line_index = 0
                if not is_sys_imported:
                    # put on SECOND line to avoid messing up the BOM:
                    if len(self.lines) > 1:
                        self.lines = ([self.lines[0]] + ["import sys"]
                                      + self.lines[1:])
                        extra_lines += 1
                    else:
                        self.lines = [self.lines[0]] + ["import sys"]
                        extra_lines += 1
                if not is_convert_note_prepended:
                    # put on SECOND line to avoid messing up the BOM:
                    if (len(self.lines) > 1):
                        self.lines = ([self.lines[0]]
                                      + [convert_note_dated]
                                      + self.lines[1:])
                        extra_lines += 1
                    else:
                        self.lines = ([self.lines[0]]
                                      + [convert_note_dated])
                        extra_lines += 1
            sr_object = None
            sr_linevar_tmp = None
            sr_linevar = None
            sw_object = None
            one_indent = "    "
            while line_index < len(self.lines):
                # self.pstat(""+participle+" line "+str(lineN)+"...")
                line_original = self.lines[line_index]
                line = line_original
                line_strip = line.strip()
                if not is_multiline_string:
                    if line_strip[:1] != "#":
                        mloi = line.find(mlD)
                        inline_comment_delimiter = "#"
                        ici = line.find(inline_comment_delimiter)
                        if (mloi > -1) and ((ici < 0) or (mloi < ici)):
                            is_multiline_string = True
                            multiline_ender_index = line.find(mlD, mloi+len(mlD))
                            if multiline_ender_index > -1:
                                is_multiline_string = False
                                self.pstat("line " + str(lineN)
                                           + ": (source notice) triple-"
                                           "quoted string (or comment)"
                                           " ended on same line as"
                                           " started")
                            else:
                                mlsv = line[mloi+len(mlD):]
                                mlsName = line[:mloi].strip()
                                mlsN = lineN
                                if len(mlsName) > 0:
                                    for ao in ["+=", "="]:
                                        if mlsName[-len(ao)] == ao:
                                            mlao = ao
                                            mlsName = mlsName[0:-len(ao)].strip()
                                            if len(mlsName) < 1:
                                                mlsName = None
                                                self.pserr("line "+str(lineN)+": (source error "+participle+") expected identifier before assignment operator (required since multiline string literal is preceeded by assignment operator)")

                                else:
                                    mlsName = None
                    class_opener = "class "
                    indent_count = find_any_not(line, " \t")
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
                            # else:
                            #     if method_member_indent is None:
                            #         method_member_indent = indent
                        if is_method_bad:
                            line = "#" + line
                            self.lines[line_index] = line
                            line_strip = line.strip()
                    if (not is_multiline_string) and (line_strip[:1] != "#"):
                        # NOTE: This is not yet the command parsing--see
                        # below class and def identification for
                        # 'actual lines'.
                        if class_indent is not None:
                            if (len(line.strip()) > 0) and (len(indent) <= len(class_indent)):  # if equal, then is a global (such as variable, class, or global function)
                                self.pstat("line "+str(lineN)+": -->ended class "+class_name+" (near '"+line+"')")
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
                                    ao = "="  # assignment_operator
                                    aoi = fUNC(line, ao)
                                    # ^ aoi: assignment_operator_index
                                    lparm = None
                                    rparm = None
                                    if aoi > -1:
                                        lparm = line[0:aoi].strip()
                                        rparm = line[aoi+len(ao):]
                                    if (lparm is not None) and (len(lparm) > 0) and (rparm is not None) and (len(rparm) > 0):
                                        type_string = self.get_python_first_explicit_type_id(rparm, lineN=lineN)
                                        if parser_op == self.parser_op_preprocess:
                                            # Even if type_string is
                                            # None (undeterminate), add
                                            # it.
                                            symbol = PCTSymbol(lparm, lineN, type_identifier=type_string)
                                            symbol.class_name = class_name
                                            symbol.default_value = rparm
                                            self.symbols.append(symbol)
                                    else:

                                        self.pserr("line "+str(lineN)+": (source error "+participle+") expected '"+ao+"' then value after class member")
                                # else:
                                #     # class method (processed in
                                #     # separate case below, and parent
                                #     # class is added automatically if
                                #     # present)
                        if line_strip[:len(def_string)] == def_string:
                            method_name_opener_index = fUNC(line,
                                                            def_string)
                            method_name_ender_index = fUNC(line, "(")
                            if method_name_opener_index > -1:
                                if method_name_ender_index > (method_name_opener_index+len(def_string)):
                                    # if method_name_ender_index>):
                                    method_name = line[method_name_opener_index+len(def_string):method_name_ender_index]
                                    method_indent = indent
                                    method_number = -1
                                    if parser_op == self.parser_op_preprocess:
                                        if class_name is not None:
                                            method_number = self.get_function_number_using_dot_notation(class_name+"."+method_name)
                                        else:
                                            method_number = self.get_function_number_using_dot_notation(method_name)
                                        if method_number < 0:
                                            this_method = PCTMethod(method_name, lineN=lineN)
                                            if class_name is not None:
                                                this_method.class_name = class_name
                                            self.functions.append(this_method)
                                            method_number = len(self.functions) - 1
                                        else:
                                            is_method_bad = True
                                            line = "#" + line
                                            self.lines[line_index] = line
                                            self.pserr("line "+str(lineN)+": source WARNING: (automatically corrected) duplicate '"+method_name+"' method starting on line--commenting since redundant (you may need to fix this by hand if this overload has code you needed).")
                                    else:
                                        method_fqname = method_name
                                        if (class_name is not None):
                                            method_fqname = class_name+"."+method_name
                                        method_number = self.get_function_number_using_dot_notation(method_fqname)
                                        if method_number < 0:
                                            self.pperr("line "+str(lineN)+": (parsing error "+participle+") no method number found for method named '"+fqname+"' (was not preprocessed correctly)")
                                        # TODO: add functions to
                                        # self.custom_types[class_number
                                        # ].children instead?
                                    if (class_name is not None) and (method_name == "__init__"):
                                        # TODO: append PCTParam objects
                                        # in self.functions[
                                        # method_number] to
                                        # self.symbols[class_number].
                                        # constructor_params
                                        pass
                                    # else:
                                    #
                                    # self.pserr("  source error "+participle+" line "+str(lineN)+": couldn't find '(' after '"+def_string+"' and method name")
                                else:

                                    self.pserr("line "+str(lineN)+": (source ERROR "+participle+")'"+def_string+"' should be followed by identifier then '('")
                            # else can never happen since def_string is
                            # already detected as the start of the line
                            # in the outer case

                        elif line_strip[0:len(class_opener)] == class_opener:
                            class_opener_index = fUNC(line, class_opener)
                            class_name_index = None
                            if class_opener_index > -1:
                                class_name_index = find_any_not(line, " \t", start=class_opener_index+len(class_opener))
                            else:
                                self.pperr("line "+str(lineN)+": (parsing error "+participle+") no  class_opener for class")
                            if method_indent is not None:
                                self.pserr("line "+str(lineN)+": (source ERROR "+participle+") unexpected classname in method (or function) def")

                            class_indent = indent
                            class_ender = ":"
                            class_name_ender = "("
                            class_name_ender_index = fUNC(line, class_name_ender, start=class_name_index)
                            class_ender_index = fUNC(line, class_ender, start=class_name_index)
                            if class_name_ender_index < 0:
                                class_name_ender = ":"
                                class_name_ender_index = fUNC(line, class_name_ender, start=class_name_index)
                            class_name = None
                            if class_name_ender_index >= 0:
                                class_name = line[class_name_index:class_name_ender_index].strip()
                                if len(class_name) > 0:
                                    if parser_op == self.parser_op_preprocess:
                                        pctclass = PCTType(class_name)
                                        self.custom_types.append(pctclass)
                                        class_number = len(self.custom_types) - 1
                                    else:
                                        class_number = self.get_class_number(class_name)
                                    if parser_op == self.parser_op_remove_net_framework:
                                        netobject_subclass_marker = "(object)"
                                        if (class_name_ender == "(") and (len(line) >= (class_name_ender_index+len(netobject_subclass_marker))) and (line[class_name_ender_index:class_name_ender_index+len(netobject_subclass_marker)] == netobject_subclass_marker):
                                            line = line[:class_name_ender_index] + line[class_ender_index:]
                                            self.pinfo("line "+str(lineN)+": removing 'object' inheritance since needs .net framework")
                                    self.pstat("line "+str(lineN)+": started class "+class_name+" cache index ["+str(class_number)+"]")
                                else:

                                    self.pserr("line "+str(lineN)+": (source ERROR "+participle+") expected classname then '"+class_ender+"' after '"+class_opener+"'")
                            else:
                                self.pserr("line "+str(lineN)+": (source ERROR "+participle+") expected  '"+class_ender+"' after '"+class_opener+"' and classname")
                        else:
                            # region actual processing of lines that are neither def nor class nor comment (put framework removal in parser_op_remove_net_framework case further down)
                            ici = find_unquoted_even_commented(line, "#")
                            nonspace_index = find_any_not(line, " \t")
                            if parser_op == self.parser_op_preprocess:
                                if (line_strip == "except , :"):
                                    line = indent + "except:"
                                    self.lines[line_index] = line
                                if (fUNC(line, "except ") > -1) or (fUNC(line, "except:") > -1) or (fUNC(line, "finally:") > -1):
                                    next_line_indent = None
                                    except_string = "except"
                                    if (fUNC(line, "finally:") > -1):
                                        except_string = "finally"
                                    next_line_number = self.find_line_nonblank_noncomment(line_index+1)
                                    if next_line_number > -1:
                                        next_line_indent = get_indent_string(self.lines[next_line_number])
                                    # self.pinfo("line "+str(lineN)+": CHECKING FOR DANGLING EXCEPTION OPENER...")
                                    if (next_line_number < 0) or (len(next_line_indent) <= len(indent)):
                                        if line_index+1 < len(self.lines):
                                            self.lines.insert(line_index+1, indent+one_indent+"pass")
                                            extra_lines += 1
                                        elif line_index+1 == len(self.lines):
                                            self.lines.append(indent+one_indent+"pass")
                                            extra_lines += 1
                                        self.pserr("line "+str(lineN)+": (WARNING: source error automatically corrected) expected indent after '"+except_string+"' so adding 'pass'")
                                # if method_name is not None:
                                # class_name_thendot = ""
                                # if class_name is not None:
                                #     class_name_thendot = class_name + "."
                                local_assn_op_index = fUNC(line, "=")
                                if local_assn_op_index > -1:
                                    identifier_last_index = find_any_not(line, " \t", start=local_assn_op_index-1, step=-1)
                                    # print("    local_assn_op_index-1:"+str(local_assn_op_index-1))
                                    # print("    identifier_last_index:"+str(identifier_last_index))
                                    if (identifier_last_index > -1) and (line[identifier_last_index] in identifier_chars):
                                        identifier_ender_index = identifier_last_index + 1
                                        local_assn_op_left = line[:identifier_ender_index].strip()
                                        if (is_identifier_valid(local_assn_op_left, True)):
                                            local_assn_op_right = line[local_assn_op_index+1:].strip()
                                            try_constructor = "StreamWriter"
                                            try_constructor_opener = try_constructor + "("
                                            if local_assn_op_right[:len(try_constructor_opener)] == try_constructor_opener:
                                                # this_symbol = PCTSymbol(local_assn_op_left, lineN, type_identifier=try_constructor)
                                                # this_symbol.method_name = method_name
                                                # this_symbol.class_name = class_name
                                                if try_constructor == "StreamWriter":
                                                    self.sw_object_strings.append(local_assn_op_left)
                                                    # input("line "+str(lineN)+": got NEW "+try_constructor+" '"+local_assn_op_left+"'--press enter")
                                            # else:
                                            #     input("line "+str(lineN)+": got new "+local_assn_op_right[:len(try_constructor_opener)]+" '"+local_assn_op_left+"'--press enter")
                                    # else:
                                    #    self.pserr("line "+str(lineN)+": (source ERROR) expected variable before '='")
                                    #    input("press enter...")
                                if method_name == "__init__":
                                    if class_name is not None:
                                        member_opener = "self."
                                        member_opener_index = fUNC(line, member_opener)
                                        if member_opener_index > -1:
                                            ao = "="
                                            aoi = fUNC(line, ao, start=member_opener_index+len(member_opener))
                                            if aoi > member_opener_index:
                                                lparm = line[0:aoi].strip()
                                                rparm = line[aoi+len(ao):]
                                                if ici > -1:
                                                    rparm = line[aoi+len(ao):ici]
                                                type_id = self.get_python_first_explicit_type_id(rparm, lineN)
                                                this_member_variable = PCTSymbol(lparm[len(member_opener):], lineN, type_identifier=type_id)
                                                this_member_variable.class_name = class_name
                                                this_member_variable.value = rparm
                                                self.symbols.append(this_member_variable)
                                            else:
                                                self.pserr("line "+str(lineN)+": (source ERROR) expected '"+ao+"' then value after member '"+member_opener+"'")
                                    else:
                                        self.pinfo("line "+str(lineN)+": (source WARNING) __init__ outside of class, so not adding any constructor-specified members")
                                elif (method_name is None) and (class_name is None):
                                    # global line
                                    # check for global variable
                                    ao = "="
                                    aoi = fUNC(line, ao)
                                    if aoi > -1:
                                        lparm = line[0:aoi].strip()
                                        rparm = line[aoi+len(ao):]
                                        if lparm.find(".") < 0:
                                            if ici > -1:
                                                rparm = line[aoi+len(ao):ici]
                                                type_id = self.get_python_first_explicit_type_id(rparm, lineN)
                                                this_member_variable = PCTSymbol(lparm[len(member_opener):], lineN, type_identifier=type_id)
                                                this_member_variable.default_value = rparm
                                                self.symbols.append(this_member_variable)
                                        # else:
                                        #     changing value of a member of some object
                                    # else global statement but not value
                            # end if self.parser_op_preprocess
                            elif parser_op == self.parser_op_remove_net_framework:

                                import_net_framework = "from System"
                                if (line_strip[0:len(import_net_framework)+1] == import_net_framework+".") or (line_strip[0:len(import_net_framework)+1] == import_net_framework+" "):
                                    line = "#"+line
                                    self.pinfo("line "+str(lineN)+": commenting useless line since imports framework")
                                else:
                                    # --- REMOVE FRAMEWORK ACTUAL LINES
                                    if sr_object is not None:
                                        sr_readline = sr_object+".ReadLine()"
                                        sr_readline_index = fUNC(line, sr_readline)
                                        if sr_readline_index > -1:
                                            # input("    DETECTED '"+sr_readline+"' at "+str(sr_readline_index)+" in '"+line+"'")
                                            sr_linevar_index = -1
                                            sr_linevar_ender_index = -1
                                            if (sr_readline_index == 0) or (line[sr_readline_index-1] not in identifier_chars):
                                                sr_linevar_last_index = find_any_not(line, " \t+=", start=sr_readline_index-1, step=-1)
                                                if sr_linevar_last_index > -1:
                                                    sr_linevar_ender_index = sr_linevar_last_index + 1
                                                    sr_linevar_index = find_any_not(line, identifier_and_dot_chars, start=sr_linevar_last_index, step=-1)
                                                    sr_linevar_index += 1
                                                    sr_linevar = line[sr_linevar_index:sr_linevar_ender_index]
                                                    sr_linevar_tmp = sr_linevar+"_with_newline"
                                                    while self.get_symbol_number_by_fqname(sr_linevar_tmp) > -1:
                                                        sr_linevar_tmp = "_" + sr_linevar_tmp
                                                else:
                                                    # input("    LINEVAR: '"+str(sr_linevar_tmp)+"' (could not find beginning of identifier ending with "+line[sr_readline_index-1]+" in '"+line+"') press enter to continue...")
                                                    pass

                                            # input("  sr_linevar = "+sr_linevar)
                                            # input("  sr_linevar_tmp = "+sr_linevar_tmp)
                                            if (sr_linevar_tmp is not None) and (len(sr_linevar_tmp) > 0):
                                                # sr_readline_after = line[sr_readline_index+len(sr_readline):]
                                                sr_readline_eof_condition = "is not None"
                                                # sr_readline_eof_condition_substringindex = fUNC(sr_readline_after,
                                                sr_readline_eof_condition_index = fUNC(line, sr_readline_eof_condition, start=sr_linevar_index+len(sr_readline_eof_condition))
                                                if sr_readline_eof_condition_index < 0:
                                                    sr_readline_eof_condition = "!= None"
                                                    sr_readline_eof_condition_index = fUNC(line, sr_readline_eof_condition, start=sr_linevar_index+len(sr_readline_eof_condition))
                                                if sr_readline_eof_condition_index < 0:
                                                    sr_readline_eof_condition = "!=None"
                                                    sr_readline_eof_condition_index = fUNC(line, sr_readline_eof_condition, start=sr_linevar_index+len(sr_readline_eof_condition))
                                                if sr_readline_eof_condition_index > -1:
                                                    line = line[:sr_readline_eof_condition_index]+"!= \"\""+line[sr_readline_eof_condition_index+len(sr_readline_eof_condition):]
                                                else:
                                                    self.pserr("line "+str(lineN)+","+str(sr_linevar_index+len(sr_readline_eof_condition))+": (source error "+participle+") expected 'is not None' after 'ReadLine' (can also use '!= None' or '!=None')")
                                                # input("    INSERTING '"+sr_linevar_tmp+"' press enter to continue...")
                                                # line = line[0:sr_linevar_index]+sr_linevar_tmp+" = "+sr_object+".readline()"+line[sr_readline_index+len(sr_readline):]
                                                line = indent+"for "+sr_linevar_tmp+" in "+sr_object+":"
                                                next_line_indent = indent+one_indent
                                                next_line_number = self.find_line_nonblank_noncomment(line_index+1)
                                                if next_line_number > -1:
                                                    next_line_indent = get_indent_string(self.lines[next_line_number])
                                                self.lines.insert(line_index+1, next_line_indent+sr_linevar+" = "+sr_linevar_tmp+".rstrip()")
                                                extra_lines += 1
                                            else:
                                                line = line[0:sr_readline_index]+sr_object+".readline()"+line[sr_readline_index+len(sr_readline)]

                                        sr_object_close = sr_object+".Close()"
                                        sr_object_close_index = fUNC(line, sr_object_close)
                                        if (sr_object_close_index == 0) or ((sr_object_close_index > -1) and (line[sr_object_close_index-1] not in identifier_chars)):
                                            sr_object_close_suffix = ""
                                            if (sr_object_close_index+len(sr_object_close)) < len(line):
                                                sr_object_close_suffix = line[sr_object_close_index+len(sr_object_close)]
                                            line = line[0:sr_object_close_index]+sr_object+".close()"+sr_object_close_suffix
                                            sr_object = None
                                            sr_linevar = None
                                            sr_linevar_tmp = None

                                    sr_class = "StreamReader"
                                    sr_start = 0
                                    while True:
                                        sr_class_index = find_identifier(line, sr_class)
                                        if sr_class_index > -1:
                                            nonspace_index = find_any_not(line, " \t", start=sr_class_index+len(sr_class))
                                            if (nonspace_index > -1) and (line[nonspace_index] == "("):
                                                parenthetical_len = get_operation_chunk_len(line, start=nonspace_index, lineN=lineN)
                                                if parenthetical_len > 0:
                                                    line = line[:sr_class_index]+"open"+line[nonspace_index:nonspace_index+parenthetical_len-1]+", 'r')"
                                                    # input("found 'StreamReader and changed line to "+line+": press enter to continue")
                                                    sr_object = line[:sr_class_index].strip()
                                                    if (sr_object[len(sr_object)-1] == "="):
                                                        sr_object = sr_object[:len(sr_object)-1].strip()
                                                        nonid_index = find_any_not(sr_object, identifier_and_dot_chars, start=len(sr_object)-1, step=-1)
                                                        if nonid_index > -1:
                                                            sr_object = sr_object[nonid_index+1:]
                                                    # input(sr_class+" object detected: "+sr_object)
                                                else:
                                                    self.pperr("line "+str(lineN)+": (parsing error "+participle+") no method params for "+sr_class)
                                                    sr_start = sr_class_index + len(sr_class)
                                                    # input("press enter to continue")
                                            else:
                                                # must be a function pointer to sr_class:
                                                sr_start = sr_class_index + len(sr_class)
                                                # input("ignoring function pointer, press enter to continue")
                                        else:
                                            # if line.find(sr_class)>-1:
                                            #     input("found class named similarly to "+sr_class+" in '"+line+"' but skipping. Press enter...")
                                            break

                                    # if sw_object is not None:
                                    for theoretical_sw_object in self.sw_object_strings:
                                        sw_writeline = theoretical_sw_object+".WriteLine("
                                        sw_writeline_index = fUNC(line, sw_writeline)
                                        if sw_writeline_index > -1:
                                            # input("    DETECTED '"+sw_writeline+"' at "+str(sw_writeline_index)+" in '"+line+"'")
                                            sw_writeline_oparen_index = sw_writeline_index+len(sw_writeline)-1
                                            sw_writeline_parenthetical_len = get_operation_chunk_len(line, start=sw_writeline_oparen_index, lineN=lineN)
                                            if (sw_writeline_parenthetical_len > 0) and (line[sw_writeline_oparen_index+sw_writeline_parenthetical_len-1] == ")"):
                                                sw_params_index = sw_writeline_index+len(sw_writeline)
                                                sw_params_ender_index = sw_writeline_oparen_index+sw_writeline_parenthetical_len-1
                                                sw_newline_string = "+\"\\n\""
                                                if (sw_params_ender_index-sw_params_index) < 1:
                                                    sw_newline_string = "\"\\n\""
                                                line = line[:sw_writeline_index+len(theoretical_sw_object)] + ".write(" + line[sw_params_index:sw_params_ender_index] + sw_newline_string + line[sw_writeline_oparen_index+sw_writeline_parenthetical_len-1:]
                                            else:
                                                self.pserr("line "+str(lineN)+": (source error "+participle+") expected params after WriteLine")
                                    if sw_object is not None:
                                        sw_object_close = sw_object+".Close()"
                                        sw_object_close_index = fUNC(line, sw_object_close)
                                        if (sw_object_close_index == 0) or ((sw_object_close_index > -1) and (line[sw_object_close_index-1] not in identifier_chars)):
                                            sw_object_close_suffix = ""
                                            if (sw_object_close_index+len(sw_object_close)) < len(line):
                                                sw_object_close_suffix = line[sw_object_close_index+len(sw_object_close)]
                                            line = line[0:sw_object_close_index]+sw_object+".close()"+sw_object_close_suffix
                                            sw_object = None


                                    sw_class = "StreamWriter"
                                    sw_start = 0
                                    while True:
                                        sw_class_index = find_identifier(line, sw_class)
                                        if sw_class_index > -1:
                                            nonspace_index = find_any_not(line, " \t", start=sw_class_index+len(sw_class))
                                            if (nonspace_index > -1) and (line[nonspace_index] == "("):
                                                parenthetical_len = get_operation_chunk_len(line, start=nonspace_index, lineN=lineN)
                                                if parenthetical_len > 0:
                                                    line = line[:sw_class_index]+"open"+line[nonspace_index:nonspace_index+parenthetical_len-1]+", 'r')"
                                                    # input("found 'StreamReader and changed line to "+line+": press enter to continue")
                                                    sw_object = line[:sw_class_index].strip()
                                                    if (sw_object[len(sw_object)-1] == "="):
                                                        sw_object = sw_object[:len(sw_object)-1].strip()
                                                        nonid_index = find_any_not(sw_object, identifier_and_dot_chars, start=len(sw_object)-1, step=-1)
                                                        if nonid_index > -1:
                                                            sw_object = sw_object[nonid_index+1:]
                                                    # input(sw_class+" object detected: "+sw_object)
                                                else:
                                                    self.pperr("line "+str(lineN)+": (parsing error "+participle+") no method params for "+sw_class)
                                                    sw_start = sw_class_index + len(sw_class)
                                                    # input("press enter to continue")
                                            else:
                                                # must be a function pointer to sw_class:
                                                sw_start = sw_class_index + len(sw_class)
                                                # input("ignoring function pointer, press enter to continue")
                                        else:
                                            # if line.find(sw_class)>-1:
                                            #     input("found class"
                                            #           " named"
                                            #           " similarly to "
                                            #           + sw_class
                                            #           + " in '" + line
                                            #           + "' but"
                                            #           " skipping."
                                            #           " Press"
                                            #           " enter...")
                                            break

                                    if exn_indent is not None:
                                        if (len(line.strip()) > 0) and (len(indent) <= len(exn_indent)):
                                            # The following commented
                                            # 'if' clause doesn't work
                                            # for some reason (ignoring,
                                            # using look-ahead instead)
                                            # if (line_index-exn_line_index<=1):
                                            #     lines.insert(
                                            #         line_index,
                                            #         exn_indent+"pass"
                                            #     )
                                            exn_indent = None
                                            exn_object_name = None
                                            exn_line_index = None
                                    if exn_indent is not None:
                                        exn_string_call = exn_object_name+".ToString()"
                                        exn_string_call_index = fUNC(line, exn_string_call)
                                        if exn_string_call_index > -1:
                                            # NOTE: Do not use
                                            # exn_object_name here,
                                            # as it was eliminated
                                            # when detected on earlier
                                            # line.
                                            fw_line = line
                                            bad_string = line[exn_string_call_index:exn_string_call_index+len(exn_string_call)]
                                            line = line[:exn_string_call_index] + exn_string + line[exn_string_call_index+len(exn_string_call):]
                                            if fw_line != line:
                                                self.pinfo("line "+str(lineN)+": (changing) using '"+exn_string+"' instead of '"+bad_string+"'")
                                    else:
                                        exn_opener_noname = "except:"
                                        exn_opener_noname_index = fUNC(line, exn_opener_noname)
                                        exn_opener = "except "
                                        exn_opener_index = fUNC(line, exn_opener)
                                        finally_opener = "finally:"
                                        finally_opener_index = fUNC(line, exn_opener)
                                        if (exn_opener_index > -1) and (exn_opener_index == indent_count):
                                            exn_line_index = line_index
                                            exn_ender_index = fUNC(line, ":", start=exn_opener_index+len(exn_opener))
                                            exn_indent = indent
                                            if exn_ender_index > -1:
                                                exn_params = explode_unquoted(line[exn_opener_index+len(exn_opener):exn_ender_index], ",")
                                                exn_identifiers = list()
                                                for exn_param_original in exn_params:
                                                    exn_param = exn_param_original.strip()
                                                    if exn_param != "Exception":
                                                        exn_identifiers.append(exn_param)
                                                if len(exn_identifiers) != 1:
                                                    self.pserr("line "+str(lineN)+": (source WARNING "+participle+") expected one exception object (got "+str(len(exn_identifiers))+": "+str(exn_identifiers)+")")
                                                if len(exn_identifiers) > 0:
                                                    exn_object_name = exn_identifiers[0]
                                                    self.pstat("line "+str(lineN)+": detected exception object--saved name as '"+exn_object_name+"'")
                                            else:
                                                self.pserr("line "+str(lineN)+": (source error "+participle+") expected colon after exception")
                                            fw_line = line
                                            line = indent + "except:"
                                            if fw_line != line:
                                                self.pinfo("line "+str(lineN)+": (changing) using 'except' instead of '"+line_strip+"'")

                                        elif (exn_opener_noname_index > -1) and (exn_opener_noname_index == indent_count):
                                            exn_line_index = line_index
                                            # exn_ender_index = fUNC(line, ":", start=exn_opener_index+len(exn_opener))
                                            exn_indent = indent
                                            exn_object_name = None

                                    start_index = 0
                                    while True:
                                        cts = "Convert.ToString"
                                        # print("  line "+str(lineN)+","+str(start_index)+": looking for "+cts)
                                        cts_new = "str"
                                        cts_index = fUNC(line, cts, start=start_index)
                                        if cts_index > -1:
                                            if (cts_index == 0) or (line[cts_index-1] not in identifier_chars):
                                                cts_ender_index = cts_index + len(cts)
                                                if (len(line) == cts_ender_index) or (line[cts_ender_index] not in identifier_chars):
                                                    line = line[:cts_index] + cts_new + line[cts_index+len(cts_new)]
                                                    start_index = cts_index + len(cts_new)
                                            else:
                                                start_index = cts_index + len(cts)
                                        else:
                                            break
                                    start_index = 0
                                    while True:
                                        fwts = "ToString"
                                        fwts_index = fUNC(line, fwts, start=start_index)
                                        if fwts_index > -1:
                                            # print("  line "+str(lineN)+","+str(start_index)+": processing "+fwts+" at column "+str(fwts_index+1))  # +" in '"+line+"'")
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
                                                        open_paren_index = fUNC(line, "(", start=fwts_index+len(fwts))
                                                        if open_paren_index > -1:
                                                            fwts_params_len = get_operation_chunk_len(line, start=open_paren_index)
                                                            if fwts_params_len > 0:
                                                                fwts_params = line[open_paren_index:open_paren_index+fwts_params_len]
                                                                fw_line = line
                                                                line = line[:operand_index]+"str("+operand+")"+line[open_paren_index+fwts_params_len:]
                                                                if fwts_params != "()":
                                                                    self.pinfo("")
                                                                    self.pinfo("line "+str(lineN)+": (parser WARNING) changing conversion to str("+operand+") but pushing off '.ToString' params ('"+fwts_params+"'; length "+str(fwts_params_len)+") to comment.")
                                                                    line += "  # "+fwts_params
                                                                elif fw_line != line:
                                                                    self.pinfo("line "+str(lineN)+": (changing) using 'str' function instead of '.ToString'")
                                                            else:
                                                                self.pserr("line "+str(lineN)+": (source ERROR) expected close parenthesis after ToString( at ["+str(fwts_index)+"]")
                                                                start_index = ftws_index + len(fwts)
                                                        else:
                                                            self.pserr("line "+str(lineN)+": (source ERROR) expected open parenthesis after ToString( at ["+str(fwts_index)+"]")
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
                                        # print("  line "+str(lineN)+","+str(start_index)+": looking for "+fwss)
                                        fwss_index = fUNC(line, fwss, start_index)
                                        if fwss_index >= 0:
                                            dot_index = fwss_index - 1
                                            if line[dot_index:dot_index+1] == ".":
                                                oparen_index = fUNC(line, "(", fwss_index+len(fwss))
                                                if oparen_index >= 0:
                                                    cparen_index = fUNC(line, ")", oparen_index+1)
                                                    if cparen_index >= 0:
                                                        params = explode_unquoted(line[oparen_index+1:cparen_index], ",")
                                                        parent_start_after_index = find_any_not(line[0:dot_index], identifier_chars, step=-1)
                                                        if parent_start_after_index >= -1:
                                                            parent_index = parent_start_after_index + 1
                                                            parent_string = line[parent_index:dot_index]
                                                            fwss_after_method = line[cparen_index+1:]
                                                            print("    parent_index:"+str(parent_index))
                                                            print("    parent_string:"+parent_string)
                                                            print("    fwss_after_method:"+fwss_after_method)

                                                            if len(params) > 1:
                                                                line = line[0:parent_index]+parent_string+"["+params[0]+":"+params[0]+"+"+params[1]+"]"+fwss_after_method
                                                            else:
                                                                line = line[0:parent_index]+parent_string+"["+params[0]+":]"+fwss_after_method
                                                            self.pinfo("line "+str(lineN)+","+str(fwss_index)+": (changing) using slices ('"+line+"') instead of Substring")
                                                        else:

                                                            self.pserr("line "+str(lineN)+": (source ERROR) expected classname before "+fwss+" at ["+str(fwss_index)+"]")
                                                            break
                                                    else:

                                                        self.pserr("line "+str(lineN)+": (source ERROR) expected unquoted ')' after "+fwss+" at ["+str(fwss_index)+"]")
                                                        break
                                                else:

                                                    self.pserr("line "+str(lineN)+": (source ERROR) expected '(' after "+fwss+" at ["+str(fwss_index)+"]")
                                                    is_mega_debug = True
                                                    oparen_index = fUNC(line, "(", fwss_index+len(fwss))
                                                    is_mega_debug = False
                                                    break
                                            else:

                                                self.pserr("line "+str(lineN)+": (source ERROR) expected '.' before "+fwss+" at ["+str(fwss_index)+"]")
                                                break
                                        else:
                                            break
                                    # end while has Substring subscripts

                                    # TODO: should use print("", file=sys.stderr):
                                    fw_line = line
                                    line = line.replace("Console.Error.WriteLine()", "sys.stderr.write(\"\\n\")")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stderr.write \\n, flush instead of Console.Error.WriteLine()")
                                        self.lines = self.lines[:line_index+1] + [indent+"sys.stderr.flush()"] + self.lines[line_index+1:]
                                        extra_lines += 1

                                    # TODO: should use print(x, file=sys.stderr):
                                    fw_line = line
                                    line = line.replace("Console.Error.WriteLine", "sys.stderr.write")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stderr.write, write \\n, flush instead of Console.Error.WriteLine")
                                        self.lines = self.lines[:line_index+1] + [indent+"sys.stderr.write(\"\\n\")", indent+"sys.stderr.flush()"] + self.lines[line_index+1:]
                                        extra_lines += 2

                                    # TODO: should sys.stderr.write(str(x)):
                                    fw_line = line
                                    line = line.replace("Console.Error.Write", "sys.stderr.write")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stderr.write instead of Console.Error.Write")
                                    fw_line = line
                                    line = line.replace("Console.Error.Flush", "sys.stderr.flush")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stderr.flush instead of Console.Error.Flush")
                                    fw_line = line
                                    line = line.replace("Console.WriteLine()", "print(\"\")")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python print instead of Console.WriteLine")
                                    line = line.replace("Console.WriteLine", "print")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python print instead of Console.WriteLine")
                                    # TODO: should sys.stdout.write(str(x)):
                                    fw_line = line
                                    line = line.replace("Console.Write", "sys.stdout.write")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stdout.write instead of Console.Write")
                                    fw_line = line
                                    line = line.replace("Console.Out.Flush", "sys.stdout.flush")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using python sys.stdout.flush instead of Console.Out.Flush")
                                    fw_line = line
                                    line = line.replace(" == None", " is None")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using ' is None' instead of ' == None'")
                                    fw_line = line
                                    line = line.replace(" != None", " is not None")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using ' is not None' instead of ' != None'")
                                    fw_line = line
                                    line = line.replace(".Replace(", ".replace(")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using '.replace(' instead of '.Replace(")
                                    fw_line = line
                                    line = line.replace(" = ArrayList(", " = list(")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using list instead of ArrayList")
                                    fw_line = line
                                    line = line.replace(".Trim()", ".strip()")
                                    if fw_line != line:
                                        self.pinfo("line "+str(lineN)+": (changing) using 'strip' instead of 'Trim'")

                                    # NOTE: lines from multiline
                                    # sections (parsed below)
                                    # must be detected in reverse order,
                                    # to preserve None value when
                                    # previous line is not present
                                    enumerable_name_prefix = "enumerator = "
                                    enumerable_name_suffix = ".GetEnumerator()"
                                    enumerator_loop = "while enumerator.MoveNext():"
                                    enumerator_current = " = enumerator.Current"

                                    enumerator_current_index = fUNC(line, enumerator_current)
                                    if enumerator_current_index >= 0:
                                        if enumerator_loop_indent is not None:
                                            fqname = arraylist_name
                                            self_identifier_then_dot = "self."
                                            if (class_name is not None) and (fqname[:len(self_identifier_then_dot)] == self_identifier_then_dot):
                                                fqname = class_name + "." + fqname[len(self_identifier_then_dot):]
                                            # should already by fully qualified, else show error intentionally:
                                            symbol_number = self.get_symbol_number_using_dot_notation(fqname)
                                            if symbol_number < 0:
                                                theoretical_name = fqname
                                                if (class_name is not None) and (not (fqname.find(".") > -1)):
                                                    theoretical_name = class_name+"._"+arraylist_name
                                                symbol_number = self.get_symbol_number_using_dot_notation(theoretical_name)
                                                if symbol_number < 0:

                                                    self.pserr("line "+str(alNameN)+": (source ERROR) used '"+fqname+"' before declaration (tried to fix as [self a.k.a.]'"+theoretical_name+"').")
                                                    if class_name is not None:
                                                        print("    class:"+class_name)
                                                    if method_name is not None:
                                                        print("    method:"+method_name)
                                                else:
                                                    self.pserr("line "+str(lineN)+": (WARNING, source error automatically corrected) used '"+arraylist_name+"' before declaration so automatically changed to existing '"+"self._"+fqname+"'.")
                                                    arraylist_name = "self._"+fqname
                                            line = enumerator_loop_indent + "for " + line[0:enumerator_current_index].strip() + " in " + arraylist_name + ":"
                                            arraylist_name = None
                                            enumerator_loop_indent = None
                                        else:

                                            self.pserr("line "+str(lineN)+": (source ERROR) unexpected '"+enumerator_current+"' (since previous line is missing '"+enumerator_loop+"' or line before that is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation) {line:"+line+"}.")
                                    else:
                                        if enumerator_loop_indent is not None:
                                            self.pserr("line "+str(lineN)+": (source ERROR) expected '"+enumerator_current+"' since '"+enumerator_loop+"' was on previous line and arraylist ("+arraylist_name+") was on line before that.")

                                        enumerator_loop_index = fUNC(line, enumerator_loop)
                                        if enumerator_loop_index >= 0:
                                            if arraylist_name is not None:
                                                enumerator_loop_indent = line[0:enumerator_loop_index]
                                                line = "#" + line
                                                self.pinfo("line "+str(lineN)+": (changing) removing useless line '"+enumerator_loop+"' (using list iteration instead)")
                                            else:
                                                enumerator_loop_indent = None
                                                self.pserr("line "+str(lineN)+": (source ERROR) unexpected '"+enumerator_loop+"' (since previous line is missing arraylist name which would have been preceded by '"+enumerable_name_prefix+"' notation).")
                                        else:
                                            enumerator_loop_indent = None
                                            if arraylist_name is not None:
                                                self.pserr("line "+str(lineN)+": (source ERROR) expected '"+enumerator_loop+"' since arraylist ("+arraylist_name+") was on previous line.")

                                            enumerable_name_prefix_index = fUNC(line, enumerable_name_prefix)
                                            if enumerable_name_prefix_index >= 0:
                                                enumerable_name_suffix_index = fUNC(line, enumerable_name_suffix, start=enumerable_name_prefix_index+len(enumerable_name_prefix))
                                                if enumerable_name_suffix_index >= 0:
                                                    arraylist_name = line[enumerable_name_prefix_index+len(enumerable_name_prefix):enumerable_name_suffix_index]
                                                    alNameN = lineN
                                                    self.pstat("line "+str(lineN)+": detected arraylist--saved name as '"+arraylist_name+"'")
                                                else:
                                                    self.pserr("line "+str(lineN)+": (source ERROR) expected '"+enumerable_name_suffix+"' after '"+enumerable_name_prefix+"'")
                                                line = "#"+line
                                            else:
                                                arraylist_name = None
                                                alNameN = None
                                    # end framework_to_standard_python
                                    # (pasted from
                                    # framework_to_standard_python
                                    # function in etc/pctdeprecated.py)
                                # end else not import System line
                            # end if self.parser_op_remove_net_framework
                            # endregion actual processing of lines that
                            # are not def or class
                        # end else neither def nor class
                    # end if not comment (nor multiline string)
                else:
                    # continue or end multiline string
                    multiline_ender_index = line.find(mlD)
                    if multiline_ender_index > -1:
                        is_multiline_string = False
                        if mlsName is not None:
                            if parser_op == self.parser_op_preprocess:
                                mlsv += line[:multiline_ender_index]
                                symbol = PCTSymbol(
                                    mlsName,
                                    mlsN,
                                    type_identifier="multiline_string",
                                    itlN=lineN
                                )
                                if class_name is not None:
                                    symbol.class_name = class_name
                                if method_name is not None:
                                    symbol.method_name = method_name
                                    if method_name == "__init__":
                                        symbol.default_value = mlsv
                                self.symbols.append(symbol)
                            # else: #TODO: track mlsv
                            # here if not preprocessing (get
                            # symbol_number using lineN)
                            mlsv = None
                            mlsName = None
                            mlsN = None
                        else:
                            if parser_op == self.parser_op_preprocess:
                                self.pstat("line " + str(lineN)
                                           + ": (source notice "
                                           + participle
                                           + ") treating"
                                           " multiline string as"
                                           " multiline comment")
                    else:
                        mlsv += line
                if outfile is not None:
                    outfile.write(line+self.newline)
                line_index += 1
                lineN = line_index + 1 - self.extra_lines_cumulative
                if extra_lines > 0:
                    self.extra_lines_cumulative += 1
                    extra_lines_passed += 1
                if extra_lines_passed >= extra_lines:
                    extra_lines = 0
                    extra_lines_passed = 0

            # end while lines
            if sw_object is not None:
                self.pserr(participle + ": source ended"
                                        " before '" + sw_object
                                        + "' (file stream) was closed")
            if is_multiline_string:
                msg = (participle + ": source ended before multiline"
                       " string or comment")
                if mlsN is not None:
                    msg += " starting on line " + str(mlsN)
                msg += " ended"
                self.pserr(msg)
            if outfile is not None:
                outfile.close()
        # end if participle is not None (no valid operation detected)
    # end process_python_lines

    def framework_to_standard_python(self, outfile_path):
        global is_mega_debug
        self.outfile_path = outfile_path
        self.process_python_lines(self.parser_op_remove_net_framework)

    def collect_python_identifiers(self, index,
                                   assignment_operator_list):
        """
        The first index returns how many lines are in the assignment
        (only works for triple-double quote syntax so far) and
        formerly called:
        'def split_assignment_line(index, assignment_operator_list):'
        """
        fUNC = find_unquoted_not_commented
        fUNCNP = find_unquoted_not_commented_not_parenthetical
        result = None
        if index < len(lines):
            line = lines[index]
            # assign_op = " = "
            # aoi = self.fUNC(assign_op)
            assign_op = None
            aoi = -1  # assignment_operator_index
            for i in range(0, len(assignment_operator_list)):
                assign_op = assignment_operator_list[i]
                aoi = fUNCNP(
                    line,
                    assign_op
                )
                if aoi >= 0:
                    break
                else:
                    assign_op = None
            if aoi >= 0:
                result = list()
                strip_assign_op_index = -1
                if assign_op is not None:
                    strip_assign_op_index = fUNC(line.strip(),
                                                 assign_op)
                if strip_assign_op_index > 0:
                    assign_left = line[0:aoi].strip()
                    assign_right = line[aoi+len(assign_op):].strip()
                    tmpRParm = assign_right
                    rparmParts = list()
                    any_delimiter = True
                    while any_delimiter:
                        any_delimiter = False
                        delimiter_index = -1
                        arithmetic_operator = None
                        for oSetI in range(0, len(self.operator_sets)):
                            oList = self.operator_sets[oSetI]
                            for operator_number in range(0, len(oList)):
                                op = oList[operator_number]
                                oi = fUNC(tmpRParm, op)
                                if delimiter_index >= 0:
                                    operand = tmpRParm[0:oi].strip()
                                    tmpRParm = tmpRParm[oi+len(op):]
                                    if len(operand) > 0:
                                        rparmParts.append(
                                            operand
                                        )
                                        self.pstat(
                                            "  found operand: "
                                            + operand
                                        )
                                    break
                                else:
                                    arithmetic_operator = None
                        if delimiter_index >= 0:
                            any_delimiter = True
                    # append last part of it (after last
                    # non-parenthetical op or if no
                    # non-parenthetical op)
                    rparmParts.append(tmpRParm.strip())
                elif strip_assign_op_index == 0:

                    self.pserr(
                        "line " + str(line_index+1) + ": (source ERROR)"
                        " unexpected assignment operator (expected"
                        " identifier first) at [" + str(aoi)
                        + "] (before identifier)"
                    )
                else:
                    self.pperr("line " + str(line_index+1)
                               + ": (parsing error)"
                               " expected assignment"
                               " operator")
        return result
    # end collect_python_identifiers

    # def get_type_identifier_recursively(line):
    #     result = None
    #     line_index = 0
    #     lineN = 1
    #     while line_index < len(self.lines):
    #         line_original = self.lines[line_index]
    #         line = line_original
    #
    #         line_index += 1
    #         lineN += 1
    #     return result

    def get_python_first_explicit_type_id(self, rparm, lineN=-1):
        """
        Sequential arguments:
        rparm -- Provide raw code to the right side of the assignment
                 operator.
        lineN -- Set the line number of the operation (starting at 1).
        """
        fUNC = find_unquoted_not_commented
        result = None
        rparm = rparm.strip()
        sign = None
        staticmethod_opener = "staticmethod("
        if rparm[:len(staticmethod_opener)] == staticmethod_opener:
            result = "staticmethod"

        if result is None:
            number_string = rparm
            if rparm[0:1] == "-":
                number_string = rparm[1:]
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
                    junk_index = find_any_not(decimal_string,
                                              digit_chars)
                    if junk_index < 0:
                        result = "decimal"
                    # TODO: make this recursive here (process operator
                    # at junk_index and all others)
                else:

                    line_display_string = "near '" + rparm + "'"
                    if lineN > 0:
                        line_display_string = "on line "+str(lineN)
                    if sign == "-":
                        self.pserr("line " + str(lineN)
                                   + ": (source ERROR)"
                                   " expected only numbers"
                                   " or '.' after '" + sign
                                   + "'")
                    # elif other_index > 0:
                    #     # this error should only displayed if
                    #     # recursion was done (such as to process
                    #     # operators):
                    #     self.pserr("  source error "
                    #                + str(lineN)
                    #                + ": only numbers or"
                    #                " '.' should be after"
                    #                " a numeric literal")
                    # else not enough information
                if (result is None) and (sign is None):
                    string_type_prefixes = ["\"", "u'", "u\"", "b'",
                                            "b\""]
                    for stp in string_type_prefixes:
                        if rparm[0:len(stp)] == stp:
                            result = "string"
                            break
            else:
                result = "int"

        if result is None:
            these_types = self.custom_types + self.builtin_types
            for this_type in these_types:
                this_type_name = this_type.name
                type_index = fUNC(rparm, this_type_name+"(")
                if type_index >= 0:
                    result = this_type
                    break
        return result
    # end get_python_first_explicit_type_id

    def get_function_number_using_dot_notation(self,
                                               fully_qualified_name):
        result = -1
        class_name = None
        method_name = fully_qualified_name
        dot_index = fully_qualified_name.find(".")
        # fqn = this_object.get_fully_qualified_name()
        # TODO: ^ ensure that misplaced line wasn't necessary in the
        # calling method
        fqn = fully_qualified_name
        if dot_index > 0:
            class_name = fully_qualified_name[0:dot_index]
            method_name = fully_qualified_name[dot_index+1:]
        for index in range(0, len(self.functions)):
            this_object = self.functions[index]
            if fully_qualified_name == this_object.name:
                if this_object.name.find(".") >= 0:
                    self.pperr("  ERROR: function '"
                               + this_object.name
                               + "' contained dot"
                               " notation (parent should"
                               " have been split during"
                               " parsing)")
                result = index
                break
            elif (fully_qualified_name == fqn):
                result = index
                break
        return result

    def get_symbol_number_using_dot_notation(self,
                                             fully_qualified_name):
        result = -1
        fqn = this_object.get_fully_qualified_name()
        for index in range(0, len(self.symbols)):
            this_object = self.symbols[index]
            if fully_qualified_name == this_object.name:
                if this_object.name.find(".") >= 0:
                    self.pperr("  ERROR: symbol '"
                               + this_object.name
                               + "' contained dot"
                               " notation (parent should"
                               " have been split during"
                               " parsing)")
                result = index
                break
            elif (fully_qualified_name == fqn):
                result = index
                break
        return result

    def find_line_nonblank_noncomment(self, start_line_number=0):
        result = -1
        # is_multiline_string = False
        line_index = start_line_number
        # ml_delimiter = "\"\"\""
        while line_index < len(self.lines):
            line_original = self.lines[line_index]
            line = line_original
            line_strip = line.strip()
            line_comment_index = find_unquoted_even_commented(line, "#")
            line_nocomment = line
            if line_comment_index > -1:
                line_nocomment = line[:line_comment_index]
            line_nocomment_strip = line_nocomment.strip()
            if len(line_nocomment_strip) > 0:
                result = line_index
                break
            line_index += 1
        return result

    # def get_parsed_symbol_by_id(sid):
    #     result = None
    #     return result

    # def name_psid(name):
    #     result = None
    #     prefix = "class["
    #     suffix = "]"
    #     for index in range(0,len(classes)):
    #         if classes[index].name==name:
    #             result = prefix+str(index)+suffix
    #             break
    #
    #     return result

    # def split_assignments_intial_only(index):
    #     assignment_operator_list = list()
    #     assignment_operator_list.append(" = ")
    #     return split_assignment_line(index, assignment_operator_list)

    # def split_assignment_line_any_assignment_method(index):
    #     assignment_operator_list = list()
    #     assignment_operator_list += (self.comparison_operators
    #                                  + self.equality_operators
    #                                  + self.assignment_operators)
    #     return split_assignment_line(index, assignment_operator_list)
