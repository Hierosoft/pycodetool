# PythonCodeTranslators
Code conversion tools, mostly just for removing dependencies so far.


## Features
### Python parsing
* Export a list of all global identifiers (after pre-processing on
  load).

### Commands
Installing the module (or installing linux-preinstall and adding
linux-preinstall/utilities and linux-preinstall/utilities-developer) to
the PATH) provides the following commands:
- `changes`: Look for repos in the current directory and show what
  changes are not yet committed (including untracked).
- `ggrep`: Get a geany command to go to the line in the file from grep
  (searching within file(s)). Recursively search directories by default.

### Python.NET to standard Python (framework_to_standard_python):
Note that GUI conversion is not tested or supported, but you can try it
the manually implement whatever is missing (or use IronPython as
necessary and not use PythonCodeTranslators).

#### STEP 1
For now, you must use SharpDevelop 4.4.
- Why: The snippet converter isn't online anymore--only a stripped down open source one is there and it only converts between C# and VB.NET. See <https://github.com/icsharpcode/CodeConverter/issues/709>.

1. Open the project in SharpDevelop (4.4 is tested). If you can't open the project, merely create a new project and add all of the C# files first.
2. Click "Project" (in the Menu bar at the top), "Convert", "From C# to Python"


See also C# to Haxe converters:
- [CS2HX](https://cs2hx.codeplex.com/releases/view/114192)
- [Phase](https://github.com/CoderLine/Phase)

(Haxe can now [output Python](https://haxe.org/manual/target-python-getting-started.html))

See also C# to Python converters:
- <https://github.com/isukces/cs2python>: Convert C# numpy code to Python numpy code properly.
- <https://github.com/poikilos/csharp-to-python>: Convert aspx properly
  (syntax only).
  - Manual changes are necessary afterward. See csharp-to-python.md

Discussions about C# to Python conversion:
- <https://www.codeproject.com/Questions/1243096/I-wanted-to-convert-Csharp-code-into-Python-code>

Non-working:
- <http://www.developerfusion.com/tools/convert/csharp-to-python/>

#### STEP 2
This step (and this project) is only necessary if you have some sort of IronPython code (such as created using SharpDevelop's C# to Python converter).

`python_remove_dotnet.py` removes non-standard Python as follows:
* Eliminates various issues and .NET calls such as introduced by SharpDevelop's C# to Python translation (formerly available in icsharpcode snippet converter)
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


## Developer Notes

### Documentation
- https://stackoverflow.com/questions/70730966/recognizing-multi-line-sections-with-lark-grammar
- https://stackoverflow.com/questions/14922242/how-to-convert-bnf-to-ebnf
- https://stackoverflow.com/questions/23456868/c-sharp-5-0-ebnf-grammar
- https://lark-parser.readthedocs.io/en/latest/parsers.html
- [Add documentation for LALR and EARLY’s differences](https://github.com/lark-parser/lark/issues/732)
- https://github.com/ligurio/lark-grammars
  - Lua

### Tools
- https://github.com/lark-parser/ide
  - live instance: https://www.lark-parser.org/ide/

### Testing
Use nose such as via `python3 -m nose` in the repo directory (requires the nose package such as via `python3 -m pip install --user nose`).
