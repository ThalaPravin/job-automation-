"""
Master Automation Orchestrator Engine
Sequentially runs Naukri, Instahyre, Wellfound, PetBiz Lead Outreach, and AutoApply ATS.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

from stats_collector import get_all_stats, print_summary

def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

class MasterOrchestrator:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or load_config()
        self.settings = self.config.get("settings", {})
        self.projects = self.config.get("projects", {})
        self.is_running = False
        self.current_task = None
        self.live_logs: List[str] = []

    def _log(self, msg: str, log_file: Optional[Path] = None, callback: Optional[Callable[[str], None]] = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        print(formatted)
        self.live_logs.append(formatted)
        if len(self.live_logs) > 3000:
            self.live_logs = self.live_logs[-2000:]
        if log_file:
            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(formatted + "\n")
        if callback:
            try:
                callback(formatted)
            except Exception:
                pass

    def run_task(self, task_key: str, command_override: Optional[List[str]] = None,
                 log_file: Optional[Path] = None,
                 callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Runs a single project automation task with live streaming output."""
        project = self.projects.get(task_key)
        if not project:
            return {
                "task": task_key,
                "status": "ERROR",
                "error": f"Unknown task: {task_key}",
                "duration": 0
            }

        name = project.get("name", task_key.upper())
        proj_dir = Path(project.get("dir", ""))
        py_exe = Path(project.get("python", ""))
        cmd_args = command_override or project.get("command", [])

        self._log("=" * 65, log_file, callback)
        self._log(f"▶ STARTING TASK: {name}", log_file, callback)
        self._log(f"  Working Directory: {proj_dir}", log_file, callback)
        self._log(f"  Python Bin:        {py_exe}", log_file, callback)
        self._log(f"  Execution Command: {' '.join(cmd_args)}", log_file, callback)
        self._log("=" * 65, log_file, callback)

        if not proj_dir.exists():
            err = f"Directory does not exist: {proj_dir}"
            self._log(f"[-] FAILED: {err}", log_file, callback)
            return {"task": task_key, "name": name, "status": "FAILED", "error": err, "duration": 0}

        if not py_exe.exists():
            err = f"Python interpreter not found: {py_exe}"
            self._log(f"[-] FAILED: {err}", log_file, callback)
            return {"task": task_key, "name": name, "status": "FAILED", "error": err, "duration": 0}

        full_cmd = [str(py_exe)] + cmd_args
        start_time = time.time()
        self.current_task = task_key

        try:
            # Launch process with unbuffered IO
            process = subprocess.Popen(
                full_cmd,
                cwd=str(proj_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            # Stream output in real-time
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    clean_line = line.rstrip()
                    if clean_line:
                        self._log(f"[{task_key.upper()}] {clean_line}", log_file, callback)

            process.wait()
            duration = round(time.time() - start_time, 2)

            if process.returncode == 0:
                self._log(f"✔ COMPLETED: {name} finished successfully in {duration}s", log_file, callback)
                return {
                    "task": task_key,
                    "name": name,
                    "status": "SUCCESS",
                    "returncode": 0,
                    "duration": duration
                }
            else:
                self._log(f"✖ FAILED: {name} exited with code {process.returncode} in {duration}s", log_file, callback)
                return {
                    "task": task_key,
                    "name": name,
                    "status": "FAILED",
                    "returncode": process.returncode,
                    "duration": duration
                }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            self._log(f"✖ EXCEPTION in {name}: {str(e)}", log_file, callback)
            return {
                "task": task_key,
                "name": name,
                "status": "ERROR",
                "error": str(e),
                "duration": duration
            }
        finally:
            self.current_task = None

    def run_daily_suite(self, task_keys: Optional[List[str]] = None,
                        callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Runs the full daily automation suite sequentially across all enabled platforms.
        Order:
        1. Naukri Booster & Apply (SDE + QA)
        2. Instahyre Booster & Apply (SDE + QA)
        3. Wellfound AI Pitch & Apply
        4. PetBiz Outreach & Follow-ups
        5. AutoApply ATS Engine (if enabled)
        """
        if self.is_running:
            return {"status": "ERROR", "message": "Another automation run is already in progress!"}

        self.is_running = True
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOGS_DIR / f"daily_run_{run_id}.log"

        if task_keys is None:
            # Default sequence
            task_keys = ["naukri", "instahyre", "wellfound", "petbiz"]
            if self.projects.get("autoapply", {}).get("enabled", False):
                task_keys.append("autoapply")

        cooldown = self.settings.get("cooldown_seconds_between_tasks", 5)
        suite_start = time.time()
        results = []

        self._log("######################################################################", log_file, callback)
        self._log(f"  🌟 STARTING UNIFIED DAILY AUTOMATION SUITE (Run ID: {run_id})", log_file, callback)
        self._log(f"  Tasks in Queue: {', '.join(task_keys)}", log_file, callback)
        self._log("######################################################################", log_file, callback)

        try:
            for idx, key in enumerate(task_keys):
                proj_cfg = self.projects.get(key, {})
                if not proj_cfg.get("enabled", True):
                    self._log(f"⏩ Skipping disabled task: {proj_cfg.get('name', key)}", log_file, callback)
                    continue

                res = self.run_task(key, log_file=log_file, callback=callback)
                results.append(res)

                # Cooldown between browser-heavy tasks
                if idx < len(task_keys) - 1 and cooldown > 0:
                    self._log(f"⏳ Cooldown pause ({cooldown}s) to allow browser session cleanup...", log_file, callback)
                    time.sleep(cooldown)

            total_duration = round(time.time() - suite_start, 2)
            self._log("======================================================================", log_file, callback)
            self._log(f"🏁 ALL DAILY AUTOMATIONS FINISHED in {total_duration}s", log_file, callback)
            self._log("======================================================================", log_file, callback)

            # Print summary report
            success_count = sum(1 for r in results if r["status"] == "SUCCESS")
            fail_count = sum(1 for r in results if r["status"] in ("FAILED", "ERROR"))
            self._log(f"📊 SUMMARY: {success_count} Succeeded, {fail_count} Failed out of {len(results)} tasks.", log_file, callback)

            # Auto-export Master CSV
            try:
                from export_master_csv import export_all
                out_p, count = export_all()
                self._log(f"📥 Master CSV updated: {count:,} applications saved to {out_p}", log_file, callback)
            except Exception as e:
                self._log(f"[-] Note: Master CSV export skipped ({e})", log_file, callback)

            return {
                "status": "COMPLETED",
                "run_id": run_id,
                "log_file": str(log_file),
                "total_duration": total_duration,
                "success_count": success_count,
                "fail_count": fail_count,
                "tasks": results
            }
        finally:
            self.is_running = False

if __name__ == "__main__":
    orchestrator = MasterOrchestrator()
    print("Master Orchestrator Engine initialized.")
