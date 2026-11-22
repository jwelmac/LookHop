@echo off
rem Runs LookHop from source in the tray, without a console window.
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" -m lookhop
