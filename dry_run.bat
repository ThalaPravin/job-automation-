@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
echo Running Wellfound Dry Run (Safe Test Mode)...
%PYTHON_CMD% main.py --dry-run --limit 3
pause
