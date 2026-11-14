@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
echo Running Wellfound Live Apply...
%PYTHON_CMD% main.py --apply --limit 10
pause
