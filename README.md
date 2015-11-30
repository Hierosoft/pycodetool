# PythonCodeTranslators
Public Licensed code conversion tools, mostly just for removing dependencies so far

## Features
### Python.NET to standard Python:
* exports list of all global identifiers (preprocesses on file load)
* Removes "from System" imports
* Removes "Exception" and uses traceback instead of calls to the exception object
* Changes "Substring" to slice notation (converts count to end)
* Fixes issues with icsharpcode snippet converter using variable and forgetting it renamed it starting with _
* Changes ArrayList iteration to list iteration
* Comments duplicate methods (and shows warning during parsing)
* Changes Console.Error.WriteLine to sys.stderr.write, write("\n"), flush
* Changes Console.Error.Write to sys.stdout.write (and ALWAYS prepends 'import sys' if not already present)
* Changes something.ToString() to str(something)
* Add 'pass' where icsharpcode converter issue leaves no indented area under 'except' or 'finally'
* Parse StreamReader (local) usage, changing 'while' to 'for', making temp variable for ReadLine and then putting temp.rstrip() into the programmer's variable
* Parse StreamWriter (scope not yet checked) changing WriteLine(something) to write(something+"\n")
* Change '.Trim()' to '.strip()'

## Known Issues
* Parse Console.Error.WriteLine(something) param, to implement print(something, file=sys.stderr) so that newline is inserted (eliminate write("\n") and flush())
* Parse StreamWriter NOTE: python automatically changes '\n' to platform-specific newline
* Account for StreamReader opened, passed as parameter (detect StreamReader and set type for method's param list), then closed after return (require second preprocessing step called param_type_determination_pass, determining params' type based on usages of function)
* Account for StreamWriter opened, passed as parameter (detect StreamReader and set type for method's param list), then closed after return (require second preprocessing step called param_type_determination_pass, determining params' type based on usages of function)
* Do not require space before equal sign (check for relative assignment operators)