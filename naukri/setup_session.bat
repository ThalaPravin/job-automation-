@echo off
cd /d "%~dp0"
set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe
if exist "..\.venv\Scripts\python.exe" set PYTHON_CMD=..\.venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

echo ===================================================
echo  Naukri 1-Time Session Login Setup
echo ===================================================
%PYTHON_CMD% setup_session.py
echo.
pause
