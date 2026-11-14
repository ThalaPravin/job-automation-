"""
Windows Task Scheduler Manager for Master Automation
Allows 1-click registration of daily automated runs at 9:00 AM (or custom time).
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import subprocess
from pathlib import Path
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent
RUN_BAT = BASE_DIR / "RUN_DAILY_ALL.bat"
TASK_NAME = "Antigravity_DailyMasterAutomation"

def get_task_status() -> str:
    """Checks whether the scheduled task is registered in Windows Task Scheduler."""
    cmd = ["schtasks", "/query", "/tn", TASK_NAME]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            lines = [l.strip() for l in res.stdout.splitlines() if TASK_NAME in l or "Ready" in l or "Running" in l]
            return f"REGISTERED & ACTIVE ({lines[0] if lines else 'Ready'})"
        return "NOT SCHEDULED"
    except Exception as e:
        return f"UNKNOWN ({e})"

def register_windows_task(trigger_time: str = "09:00") -> Tuple[bool, str]:
    """
    Registers a daily scheduled task in Windows Task Scheduler using schtasks.
    Runs every day at `trigger_time` (format HH:MM).
    """
    if not RUN_BAT.exists():
        return False, f"Launcher batch file not found at {RUN_BAT}"

    # Use schtasks.exe to create or update the task
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{str(RUN_BAT)}"',
        "/sc", "daily",
        "/st", trigger_time,
        "/f"
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, f"Successfully registered Windows Task '{TASK_NAME}' to run every day at {trigger_time}."
        else:
            err = res.stderr.strip() or res.stdout.strip()
            return False, f"Failed to register task: {err}"
    except Exception as e:
        return False, f"Error calling schtasks: {str(e)}"

def remove_windows_task() -> Tuple[bool, str]:
    """Unregisters the scheduled task."""
    cmd = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, f"Successfully removed task '{TASK_NAME}'."
        else:
            return False, f"Task not found or failed to delete: {res.stderr.strip()}"
    except Exception as e:
        return False, f"Error deleting task: {str(e)}"

if __name__ == "__main__":
    print(f"Task Scheduler Status: {get_task_status()}")
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        t = sys.argv[2] if len(sys.argv) > 2 else "09:00"
        ok, msg = register_windows_task(t)
        print(msg)
    elif len(sys.argv) > 1 and sys.argv[1] == "--remove":
        ok, msg = remove_windows_task()
        print(msg)
