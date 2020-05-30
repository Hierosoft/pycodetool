@echo off
SET PYTHON_EXE=C:\Python39\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python38\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python37\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python36\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python35\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python34\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python33\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python32\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python27\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python26\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python25\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=C:\Python24\python.exe
IF EXIST "%PYTHON_EXE%" GOTO READY
SET PYTHON_EXE=python.exe

:READY

SET try_dir=%USERPROFILE%\Documents\GitHub\blockability
SET infile_path=tests\YAMLObject_fromCodeConverter.py
SET outfile_path=%USERPROFILE%\Documents\YAMLObject.py
SET id_outfile_path=%USERPROFILE%\Documents\pycodetool last run - identifiers.txt
IF EXIST "%try_dir%\%infile_path%" SET infile_path=%try_dir%\%infile_path%
IF EXIST "%try_dir%" SET outfile_path=%try_dir%\%outfile_path%
IF EXIST "%try_dir%" SET id_outfile_path=%try_dir%\%id_outfile_path%
echo "* Writing %outfile_path% (see also %id_outfile_path%)..."
"%PYTHON_EXE%" pycodetool\python_remove_dotnet.py "%infile_path%" "%outfile_path%" "%id_outfile_path%"

pause
