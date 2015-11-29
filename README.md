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

## Known Issues
* Parse Console.Error.WriteLine(something) param, to implement print(something, file=sys.stderr) so that newline is inserted (eliminate write("\n") and flush())
* Parse StreamReader and StreamWriter NOTE: python automatically changes '\n' to platform-specific newline