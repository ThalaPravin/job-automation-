@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
echo Starting Wellfound Login in visible Chrome...
%PYTHON_CMD% main.py --login
pause
