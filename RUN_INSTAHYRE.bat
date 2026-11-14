@echo off
title Instahyre Job Automation
cd /d "%~dp0"
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

%PYTHON_CMD% main.py --instahyre
pause
