@echo off
echo If below looks right (is less than 1024 characters, and isn't truncated at the end!), try running it in a Command Prompt (Administrator):
echo setx /M PATH "%~dp0\scripts;%PATH%"
REM /M: Set it in the SYSTEM space.
REM   (Setting PATH in the user space is redundant and hinders diagnosing issues)
