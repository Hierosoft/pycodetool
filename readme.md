# PythonCodeTranslators
Code conversion tools, mostly just for removing dependencies so far.

## Features
### Python parsing
* Export a list of all global identifiers (after pre-processing on
  load).

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
See changelog.md.


## Known Issues
See also https://github.com/poikilos/PythonCodeTranslators/issues
* (wontfix) (This is not possible to fix) Correct icsharpcode snippet converter issue where even public member variables have underscore prefix (which denotes private in python)
