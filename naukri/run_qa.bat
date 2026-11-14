@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe
if exist "..\.venv\Scripts\python.exe" set PYTHON_CMD=..\.venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo ===================================================
echo  Starting QA / SDET Daily Job Automation
echo ===================================================
%PYTHON_CMD% main.py --profile qa
echo.
pause
