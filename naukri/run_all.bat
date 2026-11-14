@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe
if exist "..\.venv\Scripts\python.exe" set PYTHON_CMD=..\.venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo ===================================================
echo  Starting Daily Automation for BOTH Profiles (SDE & QA)
echo ===================================================
%PYTHON_CMD% main.py --all
echo.
pause
