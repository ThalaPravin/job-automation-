@echo off
cd /d "%~dp0"
echo Running Wellfound Dry Run (Safe Test Mode)...
.\.venv\Scripts\python main.py --dry-run --limit 3
pause
