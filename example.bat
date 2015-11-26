@echo off
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

SET try_dir=C:\Users\Owner\Documents\GitHub\blockability
SET infile_path=YAMLObject_fromCodeConverter.py
SET outfile_path=YAMLObject.py
SET id_outfile_path=last run - identifiers.txt
IF EXIST "%try_dir%\%infile_path%" SET infile_path=%try_dir%\%infile_path%
IF EXIST "%try_dir%" SET outfile_path=%try_dir%\%outfile_path%
IF EXIST "%try_dir%" SET id_outfile_path=%try_dir%\%id_outfile_path%

"%PYTHON_EXE%" python_remove_dotnet.py "%infile_path%" "%outfile_path%" "%id_outfile_path%"

pause