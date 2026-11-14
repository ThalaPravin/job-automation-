@echo off
cd /d "%~dp0"
echo Starting Wellfound Login in visible Chrome...
.\.venv\Scripts\python main.py --login
pause
