@echo off
rem First-use bootstrap launcher for Windows (Command Prompt).
rem Detects a Python 3 interpreter, then runs the cross-platform bootstrap.
setlocal
set "DIR=%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%DIR%bootstrap.py" %*
    exit /b %errorlevel%
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%DIR%bootstrap.py" %*
    exit /b %errorlevel%
)

echo Python 3.10+ is required. Install it from https://www.python.org/downloads/ and rerun this script. 1>&2
exit /b 1
