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
* Changes Console.Error.WriteLine to print
* Changes Console.Error.Write to sys.stdout.write (and ALWAYS prepends 'imports sys' if not already present)

## Known Issues
* Does not remove .ToString
