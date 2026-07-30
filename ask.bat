@echo off
rem Ask a question from the command line:
rem   ask "Why did the Western Roman Empire fall?"
rem Without arguments starts interactive mode (type 'quit' to exit).
cd /d "%~dp0"
if "%~1"=="" (
    "C:\Users\kkhee\AppData\Local\Python\bin\python.exe" src\query_cli.py
) else (
    "C:\Users\kkhee\AppData\Local\Python\bin\python.exe" src\query_cli.py -q %1 --show-context
)
