@echo off
cd /d "%~dp0"
echo Running Wellfound Live Apply...
.\.venv\Scripts\python main.py --apply --limit 10
pause
