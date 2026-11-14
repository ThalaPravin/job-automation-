@echo off
title Master Automation Interactive Dashboard
cd /d "%~dp0"
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

%PYTHON_CMD% master_automator\master_cli.py
pause
