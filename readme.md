# PythonCodeTranslators
Code conversion tools, mostly just for removing dependencies so far.

## Features
### Python parsing
* exports list of all global identifiers (preprocesses on file load)
### Python.NET to standard Python (framework_to_standard_python):
* Eliminates various issues and .NET calls such as introduced by icsharpcode snippet converter C# to Python translation
* Removes "from System" imports
* Removes "Exception" and uses traceback instead of an exception object
* Changes "Substring" to slice notation (converts count to end)
* Fixes issue with icsharpcode snippet converter using ArrayList and forgetting it renamed it starting with _
* Changes ArrayList iteration to list iteration
* Comments duplicate methods (and shows warning during parsing)
* Changes Console.Error.Write to sys.stdout.write (and ALWAYS prepends 'import sys' if not already present)
* Changes Console.WriteLine to print
* Changes Console.Error.WriteLine to sys.stderr.write, write("\n"), flush()
* Changes something.ToString() to str(something)
* Add 'pass' where icsharpcode converter issue leaves no indented area under 'except' or 'finally'
* Parse StreamReader (local) usage, changing 'while' to 'for', making temp variable for ReadLine and then putting temp.rstrip() into the programmer's variable
* Parse StreamWriter (scope not yet checked) changing WriteLine(something) to write(something+"\n")
* Change '.Trim()' to '.strip()'

## Changes
* (2015-11-33) parser_op_remove_net_framework: Removes 'object' inheritance
* (2015-11-30) Inserts note into resulting code that it was processed by this program
* (2015-11-30) Always use \n for newline, since python automatically changes instances of \n to os.sep and therefore would change os.sep to \r\r\n
* (2015-11-30) parser_op_remove_net_framework: Use WriteLine("\n") instead of WriteLine(+"\n") for streamwriter.WriteLine() with no parameters
* (2015-11-30) parser_op_remove_net_framework: Use print("") instead of print() to replace Console.Error.WriteLine() with no parameters
* (2015-11-30) parser_op_remove_net_framework: Use sys.stderr.write("\n") instead of sys.stderr.write(), write("\n"), and flush() to replace Console.Error.WriteLine() with no parameters

## Known Issues
* parser_op_remove_net_framework: Account for StreamReader opened, passed as parameter with different name (detect StreamReader and set type for method's param list), then closed after return (require second preprocessing step called param_type_determination_pass, determining params' type based on usages of function)
* parser_op_remove_net_framework: Account for StreamWriter opened, passed as parameter with different name (detect StreamReader and set type for method's param list), then closed after return (require second preprocessing step called param_type_determination_pass, determining params' type based on usages of function)
* Never require space before equal sign (check for relative assignment operators)
* Has no way of correcting icsharpcode snippet converter issue where even public member variables have underscore prefix (which denotes private in python)

## Optional improvements
* parser_op_remove_net_framework: Parse Console.Error.WriteLine(something) param, to implement print(something, file=sys.stderr) so that newline and flush occur on same line (eliminate adding write("\n") and flush())
