@echo off
title Unified Job Daily Automation Suite
cd /d "%~dp0"
set PYTHON_CMD=python
if exist "..\.venv\Scripts\python.exe" set PYTHON_CMD=..\.venv\Scripts\python.exe
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON_CMD=venv\Scripts\python.exe

echo =========================================================================
echo   STARTING UNIFIED DAILY AUTOMATION SUITE
echo   - Naukri Multi-Account Profile Booster & Apply (SDE + QA)
echo   - Instahyre Multi-Account Profile Booster & 1-Click Apply (SDE + QA)
echo   - Wellfound (AngelList) Job Applications with Gemini AI Pitch
echo =========================================================================
echo.

%PYTHON_CMD% master_cli.py --daily

echo.
echo =========================================================================
echo   Daily Automation Run Completed! Press any key to close this window.
echo =========================================================================
pause
