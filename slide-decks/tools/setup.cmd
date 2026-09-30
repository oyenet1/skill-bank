@echo off
rem Delegate version checks and private provisioning to PowerShell.
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
exit /b %errorlevel%
