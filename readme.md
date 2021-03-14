# PythonCodeTranslators
Code conversion tools, mostly just for removing dependencies so far.

## Features
### Python parsing
* Export a list of all global identifiers (after pre-processing on
  load).

### Python.NET to standard Python (framework_to_standard_python):

#### STEP 1
For now, you must use SharpDevelop 4.4.
- Why: The snippet converter isn't online anymore--only a stripped down open source one is there and it only converts between C# and VB.NET. See <https://github.com/icsharpcode/CodeConverter/issues/709>.

1. Open the project in SharpDevelop (4.4 is tested). If you can't open the project, merely create a new project and add all of the C# files first.
2. Click "Project" (in the Menu bar at the top), "Convert", "From C# to Python"


See also C# to Haxe converters:
- [CS2HX](https://cs2hx.codeplex.com/releases/view/114192)
- [Phase](https://github.com/CoderLine/Phase)

(Haxe can now [output Python](https://haxe.org/manual/target-python-getting-started.html))

See also C# to Python Converters:
- <https://github.com/isukces/cs2python> converts C# Numpy code properly (to Python Numpy)

#### STEP 2
This step (and this project) is only necessary if you have some sort of IronPython code such as created using SharpDevelop or

python_remove_dotnet.py removes non-standard Python from icsharpcode output as follows:
* Eliminates various issues and .NET calls such as introduced by icsharpcode snippet converter C# to Python translation
* Removes "from System" imports
* Removes "Exception" and uses traceback instead of an exception object
* Changes "Substring" to slice notation (converts count to end)
* Fixes issue with icsharpcode snippet converter using ArrayList and forgetting it renamed it starting with `_`
* Changes ArrayList iteration to list iteration
* Comments duplicate methods (and shows warning during parsing)
* Changes Console.Error.Write to sys.stdout.write (and ALWAYS prepends 'import sys' if not already present)
* Changes Console.WriteLine to print
* Changes Console.Error.WriteLine to sys.stderr.write, write("\n"), flush()
* Changes something.ToString() to str(something)
* Add 'pass' where icsharpcode converter issue leaves no indented area under 'except' or 'finally'
* Parse StreamReader (local) usage, changing 'while' to 'for', making temp variable for ReadLine and then putting temp.rstrip() into the programmer's variable
* Parse StreamWriter (scope not yet checked) changing `WriteLine(something)` to `write(something+"\n")`
* Change '.Trim()' to '.strip()'


## Changes
See changelog.md.


## Known Issues
See also https://github.com/poikilos/PythonCodeTranslators/issues
* (wontfix) (This is not possible to fix) Correct icsharpcode snippet converter issue where even public member variables have underscore prefix (which denotes private in python)
