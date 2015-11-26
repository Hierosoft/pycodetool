# PythonCodeTranslators
Public Licensed code conversion tools, mostly just for removing dependencies so far

## Features
### Python.NET to standard Python:
* Makes list of all global identifiers (preprocesses on file load)
* Removes "from System"
* Removes "Exception"
* Removes "Substring"
* Fixes issues with icsharpcode snippet converter using variable and forgetting it renamed it starting with _
* Changes ArrayList iteration to list iteration

## Known Issues
* Does not remove .ToString