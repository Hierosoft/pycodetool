    #merged with process_python_lines
    def framework_to_standard_python(self, outfile_path):
        global is_mega_debug
        arraylist_name = None
        enumerator_loop_indent = None
        line_index = 0
        line_counting_number = 1
        outfile = open(outfile_path, 'w')

        #post-process file:
        while line_index < len(self.lines):
            line_original = self.lines[line_index]
            line_original = line_original.strip("\n").strip("\r")
            line = line_original
            line_strip = line.strip()
            if line_strip[:1] != "#":
                #while "Substring" in line:
                import_net_framework = "from System"
                if line_strip[0:len(import_net_framework)] == import_net_framework:
                    line = "#"+line
                    print("commenting useless line "+str(line_counting_number)+" since imports framework")
                else:
                    while True:
                        fwss = "Substring"
                        fwss_index = find_unquoted_not_commented(line, fwss)
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
                                            print("  changing line "+str(line_counting_number)+","+str(fwss_index)+": using slices instead of Substring")
                                        else:
                                            print("")
                                            print("  script error on line "+str(line_counting_number)+": expected classname before "+fwss+" at ["+str(fwss_index)+"]")
                                            break
                                    else:
                                        print("")
                                        print("  script error on line "+str(line_counting_number)+": expected unquoted ')' after "+fwss+" at ["+str(fwss_index)+"]")
                                        break
                                else:
                                    print("")
                                    print("  script error on line "+str(line_counting_number)+": expected '(' after "+fwss+" at ["+str(fwss_index)+"]")
                                    is_mega_debug = True
                                    oparen_index = find_unquoted_not_commented(line, "(", fwss_index+len(fwss))
                                    is_mega_debug = False
                                    break
                            else:
                                print("")
                                print("  script error on line "+str(line_counting_number)+": expected '.' before "+fwss+" at ["+str(fwss_index)+"]")
                                break
                        else:
                            break
                    #end while has Substring subscripts
                    fw_line = line
                    line = line.replace("Console.Error.WriteLine","print")
                    if fw_line != line:
                        print("changing line "+str(line_counting_number)+": using python print instead of Console.Error.WriteLine")
                    fw_line = line
                    line = line.replace("Console.Error.Write","print")
                    if fw_line != line:
                        print("changing line "+str(line_counting_number)+": using python print instead of Console.Error.Write")
                    fw_line = line
                    line = line.replace(" == None"," is None")
                    if fw_line != line:
                        print("changing line "+str(line_counting_number)+": using ' is None' instead of ' == None'")
                    fw_line = line
                    line = line.replace(" != None"," is not None")
                    if fw_line != line:
                        print("changing line "+str(line_counting_number)+": using ' is not None' instead of ' != None'")
                    fw_line = line
                    line = line.replace(".Replace(",".replace(")
                    if fw_line != line:
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
                            self_identifier_then_dot = "self."
                            if (class_name is not None) and (fqname[:len(self_identifier_then_dot)] == self_identifier_then_dot):
                                fqname = class_name + "." + fqname[len(self_identifier_then_dot):]
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

            outfile.write(line+self.newline)
            line_index += 1
            line_counting_number += 1

        outfile.close()
    # end framework_to_standard_python
