@echo off
title Master Automation Web Control Center
cd /d "%~dp0"
set PYTHON_CMD=python
if exist "..\.venv\Scripts\python.exe" set PYTHON_CMD=..\.venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe

echo Launching Web Control Center at http://localhost:8888 ...
start "" "http://localhost:8888"
%PYTHON_CMD% web_server.py
pause
