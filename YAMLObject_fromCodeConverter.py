# 
# * Created by SharpDevelop.
# * User: jgustafson
# * Date: 3/25/2015
# * Time: 9:02 AM
# * see python version in ../../d.pygame/ via www.developerfusion.com/tools/convert/csharp-to-python
# * To change this template use Tools | Options | Coding | Edit Standard Headers.
# 
from System import *
from System.Collections import *
from System.IO import *
from System.Linq import * #Enumerable etc
#	public class YAMLLineInfo {
#		public const int TYPE_NOLINE=0;
#		public const int TYPE_OBJECTNAME=1;
#		public const int TYPE_ARRAYNAME=2;
#		public const int TYPE_ARRAYVALUE=3;
#		public const int TYPE_VARIABLE=4;
#		public int lineType=0;
#		public int lineIndex=-1;//for debugging only--line of file
#	}
class YAMLObject(object):
	""" <summary>
	 YAMLObject. The first YAMLObject object is the root (one where you call load).
	 Other YAMLObject can be either:
	 * Root is the yaml object from which you called load--normally, use this object to get values: such as myrootyamlobject.get_array_values("groups.Owner.inheritance") or myrootyamlobject.get_sub_value("groups.SuperAdmin.default").
	 * Object is stored in file like: this_name, colon, newline, additional indent, object/array/variable
	 * Array is stored in file like: this_name, colon, newline, no additional indent, hyphen, space, value
	 * Variable is stored in file like: this_name, colon, value (next line should have less or equal indent)
	 </summary>
	"""
	#public int indentCount=0;
	# <summary>
	# line from source file--for debugging only
	# </summary>
	def __init__(self):
		self._preferredYAMLQuote = "\""
		self._next_luid = 0
		self._luid = 0
		self.__name = None
		self.__value = None
		self._arrayValues = None
		self._namedSubObjects = None
		self._pre_comment_spacing = None
		self._comment = None
		self._parent = None
		self._thisYAMLSyntaxErrors = None
		self._is_verbose = False
		self._is_to_keep_spaces_outside_quotes = False
		self._indentDefaultString = "  "
		self._luid = YAMLObject.next_luid
		YAMLObject.next_luid += 1

	def clear(self):
		self.__name = None
		self.__value = None
		self._arrayValues = None
		self._namedSubObjects = None
		self._depthCount = 0
		self._indent_Length = 0
		self._indent = ""
		self._comment = None
		self._lineIndex = -1
		self._parent = None
		self._is_inline_collection = False

	def debugEnq(msg):
		if msg != None:
			if self._thisYAMLSyntaxErrors == None:
				self._thisYAMLSyntaxErrors = ArrayList()
			self._thisYAMLSyntaxErrors.Add(msg)

	debugEnq = staticmethod(debugEnq)

	def split_unquoted(haystack, field_delimiter):
		result = ArrayList()
		string_delimiter = None
		if haystack != None:
			is_escaped = False
			index = 0
			start_index = 0
			while index <= haystack.Length:
				if index == haystack.Length:
					if start_index < haystack.Length:
						result.Add(haystack.Substring(start_index))
					else:
						result.Add("") #add the empty field if ends with field_delimiter (such as, a row like ',' is considered to be two fields in any delimited format)
					break
				elif string_delimiter == None and haystack[index] == '\"' and not is_escaped:
					string_delimiter = "\""
				elif string_delimiter == None and haystack[index] == '\'' and not is_escaped:
					string_delimiter = "'"
				elif (not is_escaped) and haystack[index] == field_delimiter:
					result.Add(haystack.Substring(start_index, index - start_index)) # do not add one, since comma is not to be kept
					start_index = index + 1 #+1 to skip comma
				#result.Add(haystack.Substring(start_index, index-start_index+1));
				#below is ok since break on ==Length happens above
				if not is_escaped and haystack[index] == '\\':
					is_escaped = True
				else:
					is_escaped = False
				index += 1
		else:
			Console.Error.WriteLine("ERROR: YAMLObject split_unquoted got null haystack")
		return result

	split_unquoted = staticmethod(split_unquoted)

	#		public YAMLObject(string val)
	#		{
	#			_value=val;
	#		}
	#		public YAMLObject(string this_name, string val)
	#		{
	#			_name=this_name;
	#			_value=val;
	#		}
	#		public YAMLObject(string this_name, string val, YAMLObject Parent)
	#		{
	#			_name=this_name;
	#			_value=val;
	#			parent=Parent;
	#		}
	def split_unquoted_unbracketed_unbraced_nonparenthetical(haystack, delimiter):
		results = ArrayList()
		while haystack != None:
			if haystack == "":
				results.Add(haystack)
				haystack = None
				break
			else:
				delim_index = YAMLObject.find_unquoted_unbracketed_unbraced_nonparenthetical(haystack, delimiter)
				if delim_index > -1:
					if delim_index == 0:
						results.Add("")
						haystack = haystack.Substring(1)
					else:
						results.Add(haystack.Substring(0, delim_index))
						if delim_index == haystack.Length - 1:
							haystack = ""
						else:
							haystack = haystack.Substring(delim_index + 1)
				else:
					results.Add(haystack)
					haystack = None
					break
		return results

	split_unquoted_unbracketed_unbraced_nonparenthetical = staticmethod(split_unquoted_unbracketed_unbraced_nonparenthetical)

	def find_unquoted(haystack, needle):
		quote = None
		result = -1
		is_escaped = False
		index = 0
		while index < haystack.Length:
			if quote != None: # quoted
				if (not is_escaped) and haystack[index] == quote[0]:
					quote = None #is_escaped=false;}
				if quote == "\"" and haystack[index] == '\\':
					#only use backslash as escape if in double quotes (also, do not find needle even if needle is backslash, since in quotes)
					if not is_escaped:
						is_escaped = True
					else:
						is_escaped = False
				else: #second backslash is literal
					is_escaped = False
			else: # not quoted
				if haystack.Substring(index, needle.Length) == needle:
					result = index
					break
				elif haystack[index] == '"' or haystack[index] == '\'':
					quote = haystack.Substring(index, 1)
			index += 1
		return result

	find_unquoted = staticmethod(find_unquoted)

	def find_unquoted_unbracketed_unbraced_nonparenthetical(haystack, needle):
		enclosure_enders = ""
		openers = "({["
		closers = ")}]"
		quote = None
		result = -1
		is_escaped = False
		index = 0
		while index < haystack.Length:
			if quote != None: # quoted
				if (not is_escaped) and haystack[index] == quote[0]:
					quote = None #is_escaped=false;}
				if quote == "\"" and haystack[index] == '\\':
					#only use backslash as escape if in double quotes (also, do not find needle even if needle is backslash, since in quotes)
					if not is_escaped:
						is_escaped = True
					else:
						is_escaped = False
				else: #second backslash is literal
					is_escaped = False
			else: # not quoted
				if enclosure_enders == "" and haystack.Substring(index, needle.Length) == needle:
					result = index
					break
				elif haystack[index] == '"' or haystack[index] == '\'':
					quote = haystack.Substring(index, 1)
				elif enclosure_enders != "" and haystack.Substring(index, 1) == enclosure_enders.Substring(enclosure_enders.Length - 1, 1):
					enclosure_enders = enclosure_enders.Substring(0, enclosure_enders.Length - 1)
				else:
					enclosure_index = 0
					while enclosure_index < openers.Length:
						if haystack.Substring(index, 1) == openers.Substring(enclosure_index, 1):
							enclosure_enders += closers.Substring(enclosure_index, 1)
							break
						enclosure_index += 1
			index += 1
		return result

	find_unquoted_unbracketed_unbraced_nonparenthetical = staticmethod(find_unquoted_unbracketed_unbraced_nonparenthetical)

	def yaml_line_decode_as_inline_object(rawYAMLString, currentFileLineIndex):
		newObject = YAMLObject()
		targetObject = newObject
		#string line_value=rawYAMLString;
		if rawYAMLString == None:
			newObject._name = None
			newObject._value = None
		else:
			line_strip = rawYAMLString.Trim()
			rawYAMLString_comment_index = YAMLObject.find_unquoted(rawYAMLString, "#")
			trim_comment_index = YAMLObject.find_unquoted(line_strip, "#")
			line_Name = None
			line_Value = None
			line_no_comment = rawYAMLString
			line_trim_no_comment = line_strip
			comment_string = None
			pre_comment_spacing = None
			if rawYAMLString_comment_index > -1:
				line_no_comment = rawYAMLString.Substring(0, rawYAMLString_comment_index)
			if trim_comment_index > -1:
				line_trim_no_comment = line_strip.Substring(0, trim_comment_index)
				pre_comment_spacing_Length = line_trim_no_comment.Length - line_trim_no_comment.TrimEnd().Length
				if pre_comment_spacing_Length > 0:
					self._pre_comment_spacing = line_trim_no_comment.Substring(line_trim_no_comment.Length - pre_comment_spacing_Length)
				if trim_comment_index + 1 < line_strip.Length:
					comment_string = line_strip.Substring(trim_comment_index + 1)
				else:
					comment_string = ""
			#upon save, "#" will be re-added to comment
			colonIndex = YAMLObject.find_unquoted_unbracketed_unbraced_nonparenthetical(line_trim_no_comment, ":")
			#int indent_Length = find_any_not(line_Trim," \t"); //not relevant to inline
			if colonIndex > -1:
				if line_trim_no_comment.StartsWith("- "): # (no checking for ||line_Trim=="-" is needed, since contains colon as per outer case)
					#if (line_Trim.Length>1) {
					line_trim_no_comment = line_trim_no_comment.Substring(1).Trim()
					#}
					#else line_Trim="";
					#since has colon on same line as -:
					targetObject = YAMLObject()
					newObject.append_array_value(targetObject)
					YAMLObject.print_verbose_syntax_message("line " + (currentFileLineIndex + 1).ToString() + ": starts with '-' but has colon, so forced the variable to be a sub_object of new index in array (which is ok)")
				if colonIndex > 0:
					line_Name = line_trim_no_comment.Substring(0, colonIndex).Trim()
				else:
					line_Name = ""
					msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": missing _name before colon"
					self._thisYAMLSyntaxErrors.Add(msg)
					Console.Error.WriteLine(msg)
				#OK since already >-1:
				if colonIndex + 1 < line_trim_no_comment.Length:
					line_Value = line_trim_no_comment.Substring(colonIndex + 1).Trim()
				else:
					line_Value = ""
			else: # no assignment operator, so must be a value (part of a list or something)
				#leave _name null, since YAMLObject will null _name is used for list values in it's container YAMLObject
				if line_trim_no_comment.StartsWith("- ") or line_trim_no_comment == "-":
					if line_trim_no_comment.Length > 1:
						line_Value = line_trim_no_comment.Substring(1).Trim()
					else:
						line_trim_no_comment = ""
				else:
					line_Value = line_trim_no_comment
					msg = "YAML syntax error on line " + (currentFileLineIndex + 1).ToString() + ": missing '-' or colon for new value (block syntax is not yet implemented))"
					self._thisYAMLSyntaxErrors.Add(msg)
					Console.Error.WriteLine(msg)
			targetObject._name = line_Name
			targetObject.pre_comment_spacing = self._pre_comment_spacing
			if line_Value != None and line_Value.Length >= 2 and (line_Value[0] == '[' and line_Value[line_Value.Length - 1] == ']'):
				newObject.is_inline_collection = True #this is just for keeping output same as input
				element_strings = YAMLObject.split_unquoted_unbracketed_unbraced_nonparenthetical(line_Value.Substring(1, line_Value.Length - 2).Trim(), ",")
				#do the same things as {} since yaml_line_decode_as_inline_object is supposed to leave _name blank (this allows the user to enter a key in brackets though)
				if element_strings.Count > 0:
					enumerator = element_strings.GetEnumerator()
					while enumerator.MoveNext():
						element_string = enumerator.Current
						sub_object = YAMLObject.yaml_line_decode_as_inline_object(element_string, currentFileLineIndex)
						targetObject.append_array_value(sub_object) #since in YAMLObject, containerA:[value1,value2] is same as:
			elif 			#containerA:
			#  - value1
			#  - value2
			#leave targetObject._value null since it is a collection
line_Value != None and line_Value.Length >= 2 and line_Value[0] == '{' and line_Value[line_Value.Length - 1] == '}':
				newObject.is_inline_collection = True #this is just for keeping output same as input
				element_strings = YAMLObject.split_unquoted_unbracketed_unbraced_nonparenthetical(line_Value.Substring(1, line_Value.Length - 2).Trim(), ",")
				if element_strings.Count > 0:
					enumerator = element_strings.GetEnumerator()
					while enumerator.MoveNext():
						element_string = enumerator.Current
						sub_object = YAMLObject.yaml_line_decode_as_inline_object(element_string, currentFileLineIndex)
						targetObject.append_sub_object(sub_object)
			else: #since in YAMLObject, containerA:{nameA:value1,nameB:value2} is same as:
				#containerA:
				#  nameA:value1
				#  nameB:value2
				#leave targetObject._value null since it is a collection
				if line_Value != None:
					targetObject._value = YAMLObject.yaml_value_decode(line_Value)
			targetObject.comment = comment_string #null if no comment
		return newObject

	yaml_line_decode_as_inline_object = staticmethod(yaml_line_decode_as_inline_object)
 # end yaml_line_decode_as_inline_object
	def yaml_value_decode(rawYAMLString):
		""" <summary>
		 formerly YAMLValueFromEncoded. Based on code from expertmm.php
		 </summary>
		 <param this_name="rawYAMLString"></param>
		 <returns></returns>
		"""
		#			string thisValue = rawYAMLString;
		#			if ( (thisValue.StartsWith("\"") && thisValue.EndsWith("\""))
		#			     || (thisValue.StartsWith("'") && thisValue.EndsWith("'"))
		#			     ) {
		#				string thisQuote = thisValue.Substring(0,1);
		#				thisValue = thisValue.Substring(1,thisValue.Length-2);
		#				if (thisQuote=="'") thisValue = thisValue.Replace(thisQuote+thisQuote, thisQuote);
		#				else if (thisQuote=="\"") thisValue = thisValue.Replace("\\"+thisQuote, thisQuote);
		#			}
		#			return thisValue;
		rebuilding_string = ""
		if rawYAMLString != None:
			rawYAMLString = rawYAMLString.Trim()
			if rawYAMLString.Length == 0 or rawYAMLString == "~" or rawYAMLString == "null":
				rebuilding_string = None
			else: #everything is OK but the value translates to null
				is_prev_char_escape = False
				is_a_sequence_ender = False
				#bool IsEscape=false;//debug unnecessary variable
				if rawYAMLString.Length >= 2:
					#for handling literal quotes see http://yaml.org/spec/current.html#id2534365
					if (rawYAMLString.Substring(0, 1) == "\"") and (rawYAMLString.Substring(rawYAMLString.Length - 1, 1) == "\""):
						rawYAMLString = rawYAMLString.Substring(2, rawYAMLString.Length - 2)
						rawYAMLString = rawYAMLString.Replace("\"\"", "\"")
						#rawYAMLString=rawYAMLString.Replace("\\\"","\"");
						rebuilding_string = ""
						index = 0
						while index < rawYAMLString.Length:
							this_char_string = rawYAMLString.Substring(index, 1)
							is_a_sequence_ender = False
							if (not is_prev_char_escape) and (this_char_string == "\\"):
							else:
								#IsEscape=true;
								#IsEscape=false;
								if is_prev_char_escape:
									if (this_char_string == "0"):
										rebuilding_string += "\0"
										is_a_sequence_ender = True
									elif (this_char_string == "a"):
										rebuilding_string += Char.ToString((0x07))
										is_a_sequence_ender = True
									elif (this_char_string == "b"):
										rebuilding_string += Char.ToString((0x08))
										is_a_sequence_ender = True
									elif (this_char_string == "t"):
										rebuilding_string += "\t"
										is_a_sequence_ender = True
									elif (this_char_string == "n"):
										rebuilding_string += "\n"
										is_a_sequence_ender = True
									elif (this_char_string == "v"):
										rebuilding_string += Char.ToString((0x0B))
										is_a_sequence_ender = True
									elif (this_char_string == "f"):
										rebuilding_string += Char.ToString((0x0C))
										is_a_sequence_ender = True
									elif (this_char_string == "r"):
										rebuilding_string += "\r"
										is_a_sequence_ender = True
									elif (this_char_string == "e"):
										rebuilding_string += Char.ToString((0x1B))
										is_a_sequence_ender = True
									elif (this_char_string == "#"):
										if ((rawYAMLString.Length - index) >= 4) and (rawYAMLString.Substring(index + 1, 1) == "x"):
											rebuilding_string += Char.ToString((int.Parse(rawYAMLString.Substring(index + 2, 2))))
											index += 3 #don't go past last digit, since index will still be incremented below by 1 as usual
											is_a_sequence_ender = True
										else:
											YAMLObject.debugEnq("Invalid Escape sequence \\this_char_string since not followed by x then 2 hex digits (writing literal characters to avoid data loss)")
									elif (this_char_string == "\""):
										rebuilding_string += "\""
										is_a_sequence_ender = True
									elif (this_char_string == "/"):
										rebuilding_string += "/"
										is_a_sequence_ender = True
									elif (this_char_string == "\\"):
										rebuilding_string += "\\"
										is_a_sequence_ender = True
									elif (this_char_string == "N"):
										rebuilding_string += Char.ToString((0x85)) #unicode nextline
										is_a_sequence_ender = True
									elif (this_char_string == "_"):
										rebuilding_string += Char.ToString((0xA0)) #unicode nbsp
										is_a_sequence_ender = True
									elif (this_char_string == "L"):
										rebuilding_string += Char.ToString((0x2028)) #unicode line separator
										is_a_sequence_ender = True
									elif (this_char_string == "P"):
										rebuilding_string += Char.ToString((0x2029)) #unicode paragraph separator
										is_a_sequence_ender = True
									elif (this_char_string == "x"):
										if (rawYAMLString.Length - index) >= 3:
											rebuilding_string += Char.ToString((int.Parse(rawYAMLString.Substring(index + 1, 2))))
											index += 2 #don't go past last digit, since index will still be incremented below as usual
											is_a_sequence_ender = True
										else:
											YAMLObject.debugEnq("Invalid Escape sequence \\this_char_string since not followed by 2 hex digits (writing literal characters to avoid data loss)")
									elif (this_char_string == "u"):
										if (rawYAMLString.Length - index) >= 5:
											rebuilding_string += Char.ToString((int.Parse(rawYAMLString.Substring(index + 1, 4))))
											index += 4 #don't go past last digit, since index will still be incremented below as usual
											is_a_sequence_ender = True
										else:
											YAMLObject.debugEnq("Invalid Escape sequence \\this_char_string since not followed by 4 hex digits (writing literal characters to avoid data loss)")
									elif (this_char_string == "U"):
										if (rawYAMLString.Length - index) >= 9:
											rebuilding_string += Char.ToString((int.Parse(rawYAMLString.Substring(index + 1, 8))))
											index += 8 #don't go past last digit, since index will still be incremented below as usual
											is_a_sequence_ender = True
										else:
											YAMLObject.debugEnq("Invalid Escape sequence \\this_char_string since not followed by 8 hex digits (writing literal characters to avoid data loss)")
									else:
										YAMLObject.debugEnq("Invalid Escape sequence \\this_char_string (writing literal characters to avoid data loss)") #end if prev char is escape;
								if not is_a_sequence_ender:
									if is_prev_char_escape:
										rebuilding_string += "\\" + this_char_string
									else: # add the escape character and the literal since no escape sequence after escape character
										rebuilding_string += this_char_string # is just a literal
							if (not is_prev_char_escape) and (this_char_string == "\\"):
								is_prev_char_escape = True
							else:
								is_prev_char_escape = False
							index += 1 #even if current character is backslash, it is not the actual escape unless the case above is true
					elif (rawYAMLString.Length >= 2) and (rawYAMLString.Substring(0, 1) == "'") and (rawYAMLString.Substring(rawYAMLString.Length - 1, 1) == "'"):
						rawYAMLString = rawYAMLString.Substring(1, rawYAMLString.Length - 2)
						rawYAMLString = rawYAMLString.Replace("''", "'")
						#rawYAMLString=rawYAMLString.Replace("\\'","'");
						rebuilding_string = rawYAMLString
					else:
						rebuilding_string = rawYAMLString
				else:
					#rawYAMLString=rawYAMLString.Replace("\r\n","\n");
					#rawYAMLString=rawYAMLString.Replace("\n\r","\n");
					#rawYAMLString=rawYAMLString.Replace("\r","\n");
					rebuilding_string = rawYAMLString
		else:
			rebuilding_string = None
			Console.Error.WriteLine("PROGRAMMER ERROR: yaml_value_decode got null, so the method was misused, since unparsed YAML is text and nothing is really null, it is just left blank (zero-length string following colon), or said to be 'null' or '~'")
		return rebuilding_string

	yaml_value_decode = staticmethod(yaml_value_decode)
 #end yaml_value_decode
	def yaml_value_encode(actualValue):
		""" <summary>
		 formerly YAMLEncodedFromValue. Based on code from expertmm.php
		 </summary>
		 <param this_name="actualValue"></param>
		 <returns></returns>
		"""
		#			string rawYAMLString = actualValue;
		#			string thisQuote = preferredYAMLQuote;
		#			if (rawYAMLString.Contains("\"") || rawYAMLString.Contains("'")) {
		#				if (thisQuote=="'") {
		#					if (rawYAMLString.Contains("'")) rawYAMLString=rawYAMLString.Replace("'","''");
		#					rawYAMLString = "'"+rawYAMLString+"'";
		#				}
		#				else if (thisQuote=="\"") {
		#					if (rawYAMLString.Contains("\\")) rawYAMLString = rawYAMLString.Replace("\\","\\\\");
		#					if (rawYAMLString.Contains("\"")) rawYAMLString = rawYAMLString.Replace("\"","\\\"");
		#					rawYAMLString = "\""+rawYAMLString+"\"";
		#				}
		#				else {
		#					Console.Error.WriteLine("ERROR in yaml_value_encode--unknown preferredYAMLQuote:"+preferredYAMLQuote);
		#				}
		#			}
		#			return rawYAMLString;
		rebuilding_string = ""
		if actualValue != None:
			if actualValue.Length > 0:
				if not self._is_to_keep_spaces_outside_quotes:
					actualValue = actualValue.Trim()
				is_double_quote = False
				if (actualValue.Length >= 2) and (actualValue.Substring(0, 1) == "[") and (actualValue.Substring(actualValue.Length - 1, 1) == "]"):
					is_double_quote = True #since is assumed to not be a real array, but a string that looks like array (array should be split before calling this method)
				rebuilding_string = actualValue
				if rebuilding_string.Contains("\\"):
					rebuilding_string = rebuilding_string.Replace("\\", "\\\\")
					is_double_quote = True
				elif rebuilding_string.Contains("\0"):
					rebuilding_string = rebuilding_string.Replace("\0", "\\0")
					is_double_quote = True
				elif rebuilding_string.Contains("\u0007"):
					rebuilding_string = rebuilding_string.Replace("\u0007", "\\a")
					is_double_quote = True
				elif rebuilding_string.Contains("\u0008"):
					rebuilding_string = rebuilding_string.Replace("\u0008", "\\b")
					is_double_quote = True
				elif rebuilding_string.Contains("\t"):
					rebuilding_string = rebuilding_string.Replace("\t", "\\t")
					is_double_quote = True
				elif rebuilding_string.Contains("\n"):
					rebuilding_string = rebuilding_string.Replace("\n", "\\n")
					is_double_quote = True
				elif rebuilding_string.Contains("\u000B"):
					rebuilding_string = rebuilding_string.Replace("\u000B", "\\v")
					is_double_quote = True
				elif rebuilding_string.Contains("\u000C"):
					rebuilding_string = rebuilding_string.Replace("\u000C", "\\f")
					is_double_quote = True
				elif rebuilding_string.Contains("\r"):
					rebuilding_string = rebuilding_string.Replace("\r", "\\r")
					is_double_quote = True
				elif rebuilding_string.Contains("\u001B"):
					rebuilding_string = rebuilding_string.Replace("\u001B", "\\e")
					is_double_quote = True
				elif self._is_to_keep_spaces_outside_quotes and (rebuilding_string.Contains("\u0020")):
					rebuilding_string = rebuilding_string.Replace("\u0020", "\\x20")
					is_double_quote = True
				elif rebuilding_string.Contains("\""):
					rebuilding_string = rebuilding_string.Replace("\"", "\\\"")
					is_double_quote = True
				elif rebuilding_string.Contains("/"):
					rebuilding_string = rebuilding_string.Replace("/", "\\/")
					is_double_quote = True
				elif 				#NOTE: backslash was done first since backslashes are being added
rebuilding_string.Contains("\u0085"):
					rebuilding_string = rebuilding_string.Replace("\u0085", "\\N") #unicode nextline
					is_double_quote = True
				elif rebuilding_string.Contains("\u00A0"):
					rebuilding_string = rebuilding_string.Replace("\u00A0", "\\_") #unicode nbsp
					is_double_quote = True
				elif rebuilding_string.Contains("\u2028"):
					rebuilding_string = rebuilding_string.Replace("\u2028", "\\L") #unicode line separator
					is_double_quote = True
				elif rebuilding_string.Contains("\u2029"):
					rebuilding_string = rebuilding_string.Replace("\u2029", "\\P") #unicode paragraph separator
					is_double_quote = True
				#TODO: finish this by implementing all non-text characters using \x \u or \U escape sequences as per http://yaml.org/spec/1.2/spec.html#id2776092
				if is_double_quote:
					rebuilding_string = "\"" + rebuilding_string + "\""
			else:
				rebuilding_string = "\"\""
		else:
			rebuilding_string = "~"
		return rebuilding_string

	yaml_value_encode = staticmethod(yaml_value_encode)

	def get_name_else_blank(self):
		return self.__name if (self.__name != None) else ""

	def contains_key(self, this_name):
		found = False
		enumerator = namedSubObjects.GetEnumerator()
		while enumerator.MoveNext():
			thisYO = enumerator.Current
			if (thisYO != None) and (thisYO._name == this_name):
				found = True
				break
		return found

	def get_full__name(self):
		return self.get_full__name_recursive_DontCallMeDirectly(self.__name)

	def get_full__name_recursive_DontCallMeDirectly(self, child):
		if self.is_root():
			return child
		else:
			return self._parent.get_full__name_recursive_DontCallMeDirectly(self.__name + "." + child)

	def set_or_create(self, this_name, new_value):
		""" <summary>
		 This should always be called using the root YAMLObject (the one from which you loaded a YAML file).
		 Sub-objects should be accessed using dot notation.
		 </summary>
		 <param this_name="_name">object this_name (must be in dot notation if indented more, such as groups.Administrator.default)</param>
		 <returns></returns>
		"""
		if this_name != None:
			if this_name.Length > 0:
				foundObject = self.get_object(this_name)
				if foundObject == None:
					self.create_object(this_name)
					foundObject = self.get_object(this_name)
				if foundObject != None:
					foundObject._value = new_value
				else:
					Console.Error.WriteLine("set_or_create error: set_or_create could neither find nor create an object (this should never happen) {this_name:\"" + this_name.Replace("\"", "\\\"") + "\"}.")
			else:
				Console.Error.WriteLine("Programmer error: set_or_create cannot do anything since this_name is empty (0-length).")
		else:
			Console.Error.WriteLine("Programmer error: set_or_create cannot do anything since this_name is null")

	def get_object(self, this_name):
		foundObject = None
		if this_name != None:
			if this_name.Length > 0:
				dotIndex = -1
				nameSub = None
				if dotIndex >= 0:
					nameSub = this_name.Substring(dotIndex + 1).Trim()
					this_name = this_name.Substring(0, dotIndex).Trim()
				if self._namedSubObjects != None:
					enumerator = namedSubObjects.GetEnumerator()
					while enumerator.MoveNext():
						thisObject = enumerator.Current
						if thisObject._name == this_name:
							if nameSub != None:
								foundObject = thisObject.get_object(nameSub)
							else:
								foundObject = thisObject
							break
			else:
				Console.Error.WriteLine("Programmer error: get_object cannot do anything since this_name is empty (0-length).")
		else:
			Console.Error.WriteLine("Programmer error: get_object cannot do anything since this_name is null.")
		return foundObject
 #end get_object
	#public void set_or_create(string this_name, string new_value) {
	#	if (get_object(this_name) == null) create_object(this_name);
	#	set_or_create(this_name, new_value);
	#}
	def create_object(self, this_name):
		dotIndex = -1
		nameSub = None
		if this_name != None:
			this_name = this_name.Trim()
			dotIndex = this_name.IndexOf(".")
			if dotIndex >= 0:
				nameSub = this_name.Substring(dotIndex + 1).Trim()
				this_name = this_name.Substring(0, dotIndex).Trim()
			if this_name.Length > 0:
				newObject = None
				newObject = self.get_object(this_name)
				if newObject == None:
					newObject = YAMLObject()
					newObject._name = this_name
					newObject.parent = self
					if self._namedSubObjects == None:
						self._namedSubObjects = ArrayList()
					self._namedSubObjects.Add(newObject)
				if nameSub != None:
					newObject.create_object(nameSub)
			else:
				Console.Error.WriteLine("Programmer error: create_object cannot do anything since this_name is empty (0-length) string.")
		else:
			Console.Error.WriteLine("Programmer error: create_object cannot do anything since this_name is null.")

	#		public void append_array_value(string val) {
	#			if (arrayValues==null) arrayValues=new ArrayList();
	#			if (val!=null) arrayValues.Add(new YAMLObject(null,val));
	#			else arrayValues.Add(new YAMLObject(null,null));//allowed for situations such as where line.Trim()=="-" (item in an array of collections)
	#			//Console.Error.WriteLine("WARNING: append_array_value skipped null value.");
	#		}
	def append_array_value(self, val):
		""" <summary>
		 formerly addArrayValue
		 </summary>
		 <param this_name="val"></param>
		"""
		if self._arrayValues == None:
			self._arrayValues = ArrayList()
		if val != None:
			self._arrayValues.Add(val)
		else:
			self._arrayValues.Add(val) #allowed for situations such as where line.Trim()=="-" (item in an array of collections)
		val.parent = self

	#Console.Error.WriteLine("WARNING: append_array_value skipped null value.");
	def is_array(self):
		return self._arrayValues != None

	def dump_to_stderr(self):
		self._dump_to_stderr_recursive(None)

	def _dump_to_stderr_recursive(self, indent):
		sub_indent = ""
		if indent == None:
			sub_indent = ""
			indent = ""
		else:
			sub_indent = indent.Replace("-", " ") + "  "
		msg = indent
		indent = indent.Replace("-", " ") #after using the hyphen, it's done
		if self.__name != None:
			msg += self.__name + ":"
		parent_string = ""
		parent_id_string = ""
		value_string = ""
		array_length = 0
		if self._arrayValues != None:
			array_length = self._arrayValues.Count
		subs_length = 0
		if self._namedSubObjects != None:
			subs_length = self._namedSubObjects.Count
		if self._parent != None:
			if self._parent._name != None:
				parent_string = self._parent._name + ":"
			if self._parent._value != None:
				parent_string += self._parent._value
			parent_id_string = " parent.luid=\"" + self._parent.luid.ToString() + "\""
			#parent_string="<root>";
			if self._parent.parent == None:
				parent_id_string += " parent.type=\"root\""
		#else sub_indent="";
		if self.__value != None:
			value_string = self.__value
		msg += "<span" + parent_id_string + " luid=\"" + self._luid.ToString() + "\" parent.name=\"" + parent_string + "\""
		if array_length > 0:
			msg += " array_length=" + array_length.ToString()
		if subs_length > 0:
			msg += " subs_length=" + subs_length.ToString()
		msg += ">" + value_string + "</span>"
		#else msg+="<span id=\""+luid.ToString()+"\" parent.id=\""+parent_id_string+"\" type=\"value\" parent=\""+parent_string+"\"></span>";
		#if (this.parent!=null)
		Console.Error.WriteLine(msg)
		#if (!string.IsNullOrEmpty(msg))
		#if (this._name!=null||this._value!=null)
		msg = ""
		if self._arrayValues != None and self._arrayValues.Count > 0:
			enumerator = self._arrayValues.GetEnumerator()
			while enumerator.MoveNext():
				sub_object = enumerator.Current
				#					msg=indent+"  - ";
				#					if (sub_object._value!=null) msg+=sub_object._value;
				#					Console.WriteLine(msg);
				if sub_object != None:
					#						if (sub_object._name!=null) msg+=sub_object._name+"<ERROR--sub_object MUST NOT have _name>";
					#						if (sub_object._value!=null) msg+=sub_object._value;
					#						Console.Error.WriteLine(msg);
					sub_object._dump_to_stderr_recursive(sub_indent + "- ")
				else:
					msg = sub_indent + "- <null type=YAMLObject in=arrayValues note=\"this should never happen\">"
					Console.Error.WriteLine(msg)
		if self._namedSubObjects != None and self._namedSubObjects.Count > 0:
			enumerator = self._namedSubObjects.GetEnumerator()
			while enumerator.MoveNext():
				sub_object = enumerator.Current
				msg = "" #msg=indent+"  ";
				if sub_object != None:
					#						if (sub_object._name!=null) msg+=sub_object._name;
					#						msg+=":";
					#						if (sub_object._value!=null) msg+=sub_object._value;
					#						Console.Error.WriteLine(msg);
					sub_object._dump_to_stderr_recursive(sub_indent)
				else:
					msg = sub_indent + "<null type=YAMLObject in=arrayValues note=\"this should never happen\">"
					#msg+="<ERROR--namedSubObject MUST have this_name>";
					Console.Error.WriteLine(msg)
 #end _dump_to_stderr_recursive
	def get_sub_value(self, this_name):
		""" <summary>
		 
		 </summary>
		 <param this_name="this_name">full variable this_name (with dot notation if necessary)</param>
		 <returns></returns>
		"""
		foundValue = None
		if this_name != None:
			if this_name.Length > 0:
				foundObject = self.get_object(this_name)
				if foundObject != None:
					foundValue = foundObject._value
				else:
					if self._is_verbose:
						msg = "WARNING: get_sub_value cannot get value since object named \"" + this_name.Replace("\"", "\\\"") + "\" does not exist"
						msg += " in..."
						self.dump_to_stderr()
						Console.Error.WriteLine(msg)
			else:
				Console.Error.WriteLine("Programmer error: get_sub_value cannot do anything since this_name is empty (0-length) string for...")
				self.dump_to_stderr()
		else:
			Console.Error.WriteLine("Programmer error: get_sub_value cannot do anything since this_name is null.")
		return foundValue

	def get_value(self):
		val = None
		if self._arrayValues == None:
			val = self.__value
		return val

	#formerly getSubTrees
	def get_sub_objects(self):
		thisAL = None
		if self._namedSubObjects != None:
			thisAL = ArrayList()
			enumerator = namedSubObjects.GetEnumerator()
			while enumerator.MoveNext():
				thisYT = enumerator.Current
				thisAL.Add(thisYT)
		return thisAL

	def get_array_value(self, index):
		result = None
		if self._arrayValues != None:
			if index >= 0 and index < self._arrayValues.Count:
				result = self._arrayValues[index]
		return result

	def get_array_values(self):
		thisAL = None
		if self._arrayValues != None:
			thisAL = ArrayList()
			enumerator = arrayValues.GetEnumerator()
			while enumerator.MoveNext():
				thisValue = enumerator.Current
				thisAL.Add(thisValue)
		return thisAL

	def append_sub_object(self, addObject):
		if self._namedSubObjects == None:
			self._namedSubObjects = ArrayList()
		self._namedSubObjects.Add(addObject)
		addObject.parent = self

	#public bool is_leaf() {
	#	return !is_root() && namedSubObjects==null;
	#}
	def is_root(self):
		return self._parent == None

	#		public void loadLine(string original_line, ref int currentFileLineIndex) {
	#			
	#		}
	def get_lines(file_path):
		thisAL = None
		inStream = None
		original_line = None
		try:
			inStream = StreamReader(file_path)
			thisAL = ArrayList()
			while (original_line = inStream.ReadLine()) != None:
				thisAL.Add(original_line)
			inStream.Close()
			inStream = None
		except Exception, e:
			Console.Error.WriteLine("Could not finish YAMLObject static get_lines: " + e.ToString())
			if inStream != None:
				try:
					inStream.Close()
					inStream = None
				except , :
				finally:
		finally: #don't care
		return thisAL

	get_lines = staticmethod(get_lines)

	def deq_errors_in_yaml_syntax(self):
		thisAL = self._thisYAMLSyntaxErrors
		self._thisYAMLSyntaxErrors = ArrayList()
		return thisAL

	def get_ancestor_with_indent(self, theoreticalWhitespaceCount, lineOfSibling_ForSyntaxCheckingMessage):
		ancestor = None
		if self._indent_Length == theoreticalWhitespaceCount:
			ancestor = self
			self.print_verbose_syntax_message("...this (" + self.get_debug_noun() + ") is ancestor of " + (self.__name if (not str.IsNullOrEmpty(self.__name)) else "root (assumed to be root since has blank this_name)") + " on line " + (self._lineIndex + 1).ToString() + " since has whitespace count " + self._indent_Length.ToString())
		else:
			if self._parent != None:
				IsCircularReference = False
				if self._parent.parent != None:
					if self._parent.parent == self:
						IsCircularReference = True
						msg = "YAML syntax error on line " + (lineOfSibling_ForSyntaxCheckingMessage + 1).ToString() + ": circular reference (parent of object on line " + (self._lineIndex + 1).ToString() + "'s parent is said object)."
						self._thisYAMLSyntaxErrors.Add(msg)
						Console.Error.WriteLine(msg)
				if not IsCircularReference:
					ancestor = self._parent.get_ancestor_with_indent(theoreticalWhitespaceCount, lineOfSibling_ForSyntaxCheckingMessage)
			else:
				msg = "YAML syntax error on line " + (lineOfSibling_ForSyntaxCheckingMessage + 1).ToString() + ": unexpected indent (there is no previous line with this indentation level, yet it is further back than a previous line indicating it should have a sibling)."
				self._thisYAMLSyntaxErrors.Add(msg)
				Console.Error.WriteLine(msg)
		return ancestor
 #end get_ancestor_with_indent
	def print_verbose_syntax_message(msg):
		if self._is_verbose:
			if msg != None:
				msg = "#Verbose message: " + msg
				if self._thisYAMLSyntaxErrors != None:
					self._thisYAMLSyntaxErrors.Add(msg)
				Console.Error.WriteLine(msg)

	print_verbose_syntax_message = staticmethod(print_verbose_syntax_message)

	def get_array_length(self):
		count = 0
		if self._arrayValues != None:
			count = self._arrayValues.Count
		return count

	def find_any_not(haystack, needles):
		result = -1
		if haystack != None:
			if needles != None:
				index = 0
				while index < haystack.Length:
					is_needle = False
					number = 0
					while number < needles.Length:
						if haystack[index] == needles[number]:
							is_needle = True
							break
						index += 1
					if not is_needle:
						result = index
						break
					index += 1
			else:
				Console.Error.WriteLine("null needles in YAMLObject.find_any_not")
		else:
			Console.Error.WriteLine("null haystack in YAMLObject.find_any_not")
		return result

	find_any_not = staticmethod(find_any_not)

	def parse_next_yaml_chunk(lines, debug_input_description, currentFileLineIndex, rootObject, prevLineYAMLObject):
		""" <summary>
		 Parses a line and gets the yaml object, setting the parent properly.
		 </summary>
		 <param this_name="lines"></param>
		 <param this_name="currentFileLineIndex"></param>
		 <param this_name="prevWhitespaceCount"></param>
		 <param this_name="rootObject"></param>
		 <param this_name="prevLineYAMLObject"></param>
		 <returns>A new YAML Object EXCEPT when an array element, then returns prevLineYAMLObject</returns>
		"""
		#prevLineYAMLObject must be fed back from return value of previous call
		#YAMLObject nextLineParentYAMLObject=null;
		newObject = None
		try:
			if lines != None:
				#int prevWhitespaceCount=0;
				#if (prevLineYAMLObject!=null) prevWhitespaceCount=prevLineYAMLObject.indent_Length;
				original_line = lines[currentFileLineIndex]
				line_TrimStart = original_line.TrimStart()
				line_Trim = original_line.Trim()
				indent = ""
				IsSyntaxErrorShown = False
				indent_Length = 0
				#int indent_ender = find_any_not(original_line, " \t");
				#if (indent_ender>-1) indent=original_line.Substring(0,indent_ender);
				if line_Trim.Length > 0:
					if not line_Trim.StartsWith("#"):
						self._indent_Length = original_line.Length - line_TrimStart.Length
						self._indent = original_line.Substring(0, self._indent_Length)
						#thisWhitespace=original_line.Substring(0,
						parentYO = None
						if prevLineYAMLObject != None:
							if self._indent.Length == prevLineYAMLObject.indent_Length:
								parentYO = prevLineYAMLObject.parent
								if self._is_verbose:
									parent_id_string = ""
									if parentYO.parent != None:
										parent_id_string = parentYO.luid.ToString()
									Console.Error.WriteLine("(verbose message) " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": parent (luid=" + parent_id_string + ") is previous line (luid=" + prevLineYAMLObject.luid.ToString() + ")'s parent ")
							elif self._indent.Length > prevLineYAMLObject.indent_Length:
								parentYO = prevLineYAMLObject
								if self._is_verbose:
									parent_id_string = ""
									if parentYO != None:
										parent_id_string = parentYO.luid.ToString()
									Console.Error.WriteLine("(verbose message) " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": parent (luid=" + parent_id_string + ") is previous line ")
							else:
								if self._indent.Length == 0:
									parentYO = rootObject
									Console.Error.WriteLine("(verbose message) " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": is in root (since no indent)")
								else:
									parentYO = prevLineYAMLObject.get_ancestor_with_indent(self._indent.Length - 2, currentFileLineIndex)
								if parentYO == None:
									parentYO = rootObject
									msg = "YAML syntax error on " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": object was found at an indent level not matching any previous line, so the object is being added to the root object to prevent data loss."
									IsSyntaxErrorShown = True
									self._thisYAMLSyntaxErrors.Add(msg)
									Console.Error.WriteLine(msg)
								elif self._is_verbose:
									parent_id_string = ""
									if parentYO != None:
										if parentYO.parent != None:
											parent_id_string = parentYO.luid.ToString()
										else:
											parent_id_string = "root " + parentYO.luid.ToString()
									Console.Error.WriteLine("(verbose message) " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": parent is (luid=" + parent_id_string + ") since indent Length is " + self._indent.Length.ToString() + "")
						else:
							parentYO = rootObject
							if self._is_verbose:
								parent_id_string = ""
								if parentYO != None:
									parent_id_string = parentYO.luid.ToString()
								Console.Error.WriteLine("(verbose message) " + debug_input_description + " line " + (currentFileLineIndex + 1).ToString() + ": parent (luid=" + parent_id_string + ") is root since is the first line of the file ")
						#string line_Name=null;
						#string line_Value=null;
						#if (indent_Length==prevWhitespaceCount) {
						newObject = None
						#bool is_line_array_element=false;
						if line_Trim.StartsWith("- ") or line_Trim == "-": #this line is part of an array (do not allow starting with only '-' since that could be a number)
							#line_Name=null;
							#bool IsSyntaxErrorShown=false;
							#line_Value = line_Trim.Substring(1).Trim(); //doesn't matter, since done by yaml_line_decode_as_inline_object
							newObject = YAMLObject.yaml_line_decode_as_inline_object(line_Trim, currentFileLineIndex)
							parentYO.append_array_value(newObject)
						else:
							#print_verbose_syntax_message(debug_input_description+" line "+(currentFileLineIndex+1).ToString()+"...array value at index ["+(parentYO.get_array_length()-1).ToString()+"] in "+((!string.IsNullOrEmpty(parentYO._name))?parentYO._name:"root (assumed to be root since has blank this_name)")); #end if line is an array element #this line is an object, single-value variable, or array this_name)
							newObject = YAMLObject.yaml_line_decode_as_inline_object(line_Trim, currentFileLineIndex)
							parentYO.append_sub_object(newObject) #end else line is an object or variable
						#}
						newObject.indent_Length = self._indent_Length
						newObject.indent = self._indent
						newObject.lineIndex = currentFileLineIndex
						newObject.parent = parentYO
					else:
						newObject = prevLineYAMLObject
						comment_object = newObject
						if newObject == None:
							comment_object = rootObject
						if comment_object.comment == None:
							if prevLineYAMLObject == None:
								comment_object.comment = ""
							else:
								comment_object.comment = Environment.NewLine
						else: #start with newline since line starts with comment
							comment_object.comment += Environment.NewLine #debug: this should be "\n" in python since python converts it automatically!
						comment_object.comment += 
				else: # 1 to skip comment mark
					#NOTE: during save, comments is prefixed with "#" and newline is replaced with newline+"#" #end if line_Trim.Length>0
					newObject = prevLineYAMLObject
		except Exception, e: #end if lines!=null
			msg = "YAML parser failure (parser could not finish) on line " + (currentFileLineIndex + 1).ToString() + ": " + e.ToString()
			self._thisYAMLSyntaxErrors.Add(msg)
			Console.Error.WriteLine(msg)
		finally:
		return newObject

	parse_next_yaml_chunk = staticmethod(parse_next_yaml_chunk)
 #end loadYAMLObject
	def load_yaml_lines(self, lines, debug_input_description):
		if lines != None:
			if self._thisYAMLSyntaxErrors == None:
				self._thisYAMLSyntaxErrors = ArrayList()
			else:
				self._thisYAMLSyntaxErrors.Clear()
			#int prevWhitespaceCount=0;
			#int indent_Length=0;
			currentFileLineIndex = 0
			prevObject = None
			if self._is_verbose:
				Console.Error.WriteLine("(verbose message) " + debug_input_description + "...")
			while currentFileLineIndex < lines.Length:
				prevObject = self.parse_next_yaml_chunk(lines, debug_input_description, currentFileLineIndex, self, prevObject)
				currentFileLineIndex += 1
 #end load_yaml_lines
	def load(self, file_path):
		""" <summary>
		 Top level is self, but with no this_name is needed, to allow for multiple variables--for example, if file begins with "groups," this object will have no this_name but this object's subtree will contain an object named groups, and then you can get the values like: getArrayAsStrings("groups.SuperAdmin.permissions")
		 </summary>
		 <param this_name="file_path"></param>
		"""
		thisAL = self.get_lines(file_path)
		lines = None
		if thisAL != None and thisAL.Count > 0:
			lines = Array.CreateInstance(str, thisAL.Count)
			index = 0
			newline_chars = Array[Char](('\n', '\r'))
			enumerator = thisAL.GetEnumerator()
			while enumerator.MoveNext():
				line = enumerator.Current
				lines[index] = line.Trim(newline_chars)
				index += 1
			self.load_yaml_lines(lines, file_path)
 #end load
	def save(self, file_path):
		outStream = None
		try:
			outStream = StreamWriter(file_path)
			self.save_self(outStream)
			outStream.Close()
			outStream = None
		except Exception, e:
			msg = "YAMLObject: Could not finish save: " + e.ToString()
			self.print_verbose_syntax_message(msg)
			Console.Error.WriteLine(msg)
			if outStream != None:
				try:
					outStream.Close()
					outStream = None
				except , :
				finally:
		finally:
 #don't care #end save
	def get_comment_as_yaml(pre_spacing, this_object):
		comment_string = ""
		if this_object.comment != None:
			comment_string = ""
			if this_object.comment.Length >= Environment.NewLine.Length and this_object.comment.Substring(0, Environment.NewLine.Length) == Environment.NewLine:
				comment_string = Environment.NewLine + "#" + this_object.comment.Substring(Environment.NewLine.Length).Replace(Environment.NewLine, Environment.NewLine + "#")
			else:
				comment_string = pre_spacing + "#" + this_object.comment.Replace(Environment.NewLine, Environment.NewLine + "#")
		#if (this_object.comment!=null) comment_string=this_object.comment;
		return comment_string

	get_comment_as_yaml = staticmethod(get_comment_as_yaml)

	def save_self(self, outStream):
		""" <summary>
		 assumes children are not indented, and self is root (therefore self._name and self._value are NOT written)
		 </summary>
		 <param name="outStream"></param>
		"""
		foundSubTreeCount = 0
		line = "# "
		if self.__name != None:
			line += self.__name + ":"
		if self.__value != None:
			line += self.yaml_value_encode(self.__value)
		if line == "# ":
			line = ""
		line += YAMLObject.get_comment_as_yaml("", self)
		if line != "":
			outStream.WriteLine(line)
		if self._namedSubObjects != None:
			enumerator = namedSubObjects.GetEnumerator()
			while enumerator.MoveNext():
				sub_object = enumerator.Current
				#print_verbose_syntax_message(myRealIndentString+"saving namedSubObject");
				sub_object._save_self_recursive(outStream, "", "  ") #, sub_object.is_inline_collection);
				foundSubTreeCount += 1
		count = 0
		if self._arrayValues != None:
			enumerator = arrayValues.GetEnumerator()
			while enumerator.MoveNext():
				sub_object = enumerator.Current
				prefix = "- "
				if sub_object._name == None and sub_object._value == None:
					prefix = "-"
				sub_object._save_self_recursive(outStream, "", prefix) #, sub_object.is_inline_collection);
				count += 1

	def _save_self_recursive(self, outStream, indent, prefix):
		#string thisIndentString=get_my_indent();
		line = None
		foundSubTreeCount = 0
		try:
			#string myRealIndentString=get_my_corrected_indent();
			if self.__name == None and self.__value == None and prefix == "- ":
				prefix = "-"
			line = indent + prefix
			if self.__name != None:
				line += self.__name + ":"
			if self.__value != None:
				line += self.yaml_value_encode(self.__value)
			this_pre_comment_spacing = ""
			if self._pre_comment_spacing != None:
				this_pre_comment_spacing = self._pre_comment_spacing
			line += YAMLObject.get_comment_as_yaml(this_pre_comment_spacing, self)
			if line != indent + prefix or prefix != "":
				#if (is_inline_collection) outStream.Write(line);
				#else
				outStream.WriteLine(line)
			#				if (_value!=null) {
			#					print_verbose_syntax_message("Saved variable");
			#					line=myRealIndentString+_name+": "+_value;
			#					outStream.WriteLine(line);
			#				}
			#				else {
			#					string msg="ERROR in saveSelf: null _value ("+get_debug_noun()+")";
			#					if (YAMLObject.thisYAMLSyntaxErrors==null) YAMLObject.thisYAMLSyntaxErrors=new ArrayList();
			#					YAMLObject.thisYAMLSyntaxErrors.Add(msg);
			#					Console.Error.WriteLine(msg);
			#				}
			if self._namedSubObjects != None:
				#					if (is_inline_collection) {
				#						
				#					}
				#					else {
				enumerator = namedSubObjects.GetEnumerator()
				while enumerator.MoveNext():
					sub_object = enumerator.Current
					#print_verbose_syntax_message(myRealIndentString+"saving namedSubObject");
					sub_object._save_self_recursive(outStream, indent + "  ", "")
					foundSubTreeCount += 1
				#					}
				msg = indent + "Saved " + foundSubTreeCount.ToString() + " subtrees for YAMLObject named " + self.yaml_value_encode(self.__name)
				if self._lineIndex >= 0:
					msg += " that had been loaded from line " + (self._lineIndex + 1).ToString()
				else:
					msg += " that had been generated (not loaded from a file)"
				self.print_verbose_syntax_message(msg)
				if self._arrayValues != None:
					self.print_verbose_syntax_message("line " + (self._lineIndex + 1).ToString() + ": collection with sub objects also has array values (this is outside of YAML spec)")
			if self._arrayValues != None:
				count = 0
				enumerator = arrayValues.GetEnumerator()
				while enumerator.MoveNext():
					sub_object = enumerator.Current
					sub_object._save_self_recursive(outStream, indent + "  ", "- ")
				self.print_verbose_syntax_message(indent + "Saved " + count.ToString() + "-length array")
		except Exception, e:
			msg = "Could not finish _save_self_recursive: " + e.ToString()
			Console.Error.WriteLine(msg)
			YAMLObject.thisYAMLSyntaxErrors.Add(msg)
		finally:
 #end _save_self_recursive
	def get_debug_noun(self):
		""" <summary>
		 formerly getDescription
		 </summary>
		 <returns></returns>
		"""
		typeString = "array" if (self._arrayValues != None) else "object"
		lineTypeMessage = ""
		if self._lineIndex >= 0:
			lineTypeMessage += " that had been loaded from line " + (self._lineIndex + 1).ToString()
		else:
			lineTypeMessage += " that had been generated (not loaded from a file)"
		descriptionString = typeString + " named: " + self.yaml_value_encode(self.__name) + lineTypeMessage + "; is" + ("" if (self._namedSubObjects != None) else " not") + " leaf"
		descriptionString += "; _value:" + self.yaml_value_encode(self.__value)
		descriptionString += "; parent:" + (("._name:" + self.yaml_value_encode(self._parent._name)) if (self._parent != None) else "null")
		return descriptionString

	def get_indent(count):
		val = System.String(self._indentDefaultString[0], count * self._indentDefaultString.Length)
		return val

	get_indent = staticmethod(get_indent)
 #return string.Concat(Enumerable.Repeat(indentDefaultString, count));
	def get_my_indent(self):
		return self.get_indent(self._indent_Length)

	def get_my_corrected_indent(self):
		count = self.get_my_corrected_indent_count_recursive(0)
		return self.get_indent(count)

	def get_my_corrected_indent_count_recursive(self, i):
		if self._parent != None:
			if not self._parent.is_root():
				i = self._parent.get_my_corrected_indent_count_recursive(i + 1)
		return i