"""
Naukri Job Automation Engine - Multi-Profile Orchestrator
Supports:
  - SDE Profile (Java, Backend, Software Developer)
  - QA Profile  (Automation Tester, QA, SDET)
Usage:
  python main.py --profile sde   # Run SDE automation only
  python main.py --profile qa    # Run QA automation only
  python main.py --all           # Run both profiles sequentially
"""

import sys
import os
import argparse
import yaml
from datetime import datetime

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except Exception:
            pass

from playwright.sync_api import sync_playwright

from database import init_db, get_total_stats
from browser_manager import get_persistent_context
from profile_updater import update_resume_and_profile
from job_engine import run_job_discovery

def load_config(config_path: str = "config.yaml"):
    if not os.path.exists(config_path):
        print(f"[-] Config file {config_path} not found!")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_single_profile(profile_key: str, config: dict):
    profile_cfg = config.get("profiles", {}).get(profile_key)
    if not profile_cfg:
        print(f"[-] Profile '{profile_key}' not found in config.yaml!")
        return

    name = profile_cfg.get("name", profile_key.upper())
    db_path = profile_cfg.get("db_path", f"data/naukri_{profile_key}.db")
    user_data_dir = profile_cfg.get("user_data_dir", f"browser_profile_{profile_key}")
    
    print("\n" + "=" * 65)
    print(f" STARTING PIPELINE: [{name.upper()}]")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # Initialize profile database
    init_db(db_path)

    # Check if session exists
    if not os.path.exists(user_data_dir):
        print(f"\n[!] WARNING: Persistent browser session not found for [{profile_key}].")
        print(f"Please run 'python setup_session.py --profile {profile_key}' first to log in manually.\n")
        return

    with sync_playwright() as p:
        context = get_persistent_context(p, headless=False, user_data_dir=user_data_dir)
        page = context.pages[0] if context.pages else context.new_page()

        # Step 1: Daily Resume & Profile Freshness
        if profile_cfg.get("auto_update_resume", True):
            print(f"\n--- STEP 1: RESUME REFRESH & PROFILE TIMESTAMP [{profile_key.upper()}] ---")
            update_resume_and_profile(page, config, profile_key)

        # Step 2: Job Discovery & Application Pipeline
        print(f"\n--- STEP 2: JOB DISCOVERY & APPLICATION ENGINE [{profile_key.upper()}] ---")
        results = run_job_discovery(context, config, profile_key)

        # Step 3: Reporting & Summary
        print("\n" + "=" * 65)
        print(f" DAILY RUN SUMMARY: [{name.upper()}]")
        print("=" * 65)
        print(f"  * Direct Applications Completed Today : {results['direct_applied']}")
        print(f"  * External Jobs Exported to CSV      : {results['external_saved']}")
        print(f"  * Total Processed Today               : {results['total_processed']}")
        
        overall = get_total_stats(db_path)
        print("-" * 65)
        print(f"  * Lifetime Direct Applied Tracked    : {overall['total_direct_applied']}")
        print(f"  * Lifetime External Jobs Saved       : {overall['total_external_saved']}")
        print(f"  * Lifetime Jobs in Profile Database  : {overall['total_jobs_tracked']}")
        print(f"  * CSV Output Path                    : {os.path.abspath(profile_cfg.get('external_csv_path', f'data/external_jobs_{profile_key}.csv'))}")
        print("=" * 65)

        context.close()
        print(f"\n[SUCCESS] Pipeline for [{name}] completed successfully.\n")

def main():
    parser = argparse.ArgumentParser(description="Naukri Job Automation Engine")
    parser.add_argument("--profile", choices=["sde", "qa"], default="sde", help="Target profile to execute")
    parser.add_argument("--all", action="store_true", help="Execute both SDE and QA profiles sequentially")
    args = parser.parse_args()

    config = load_config()

    if args.all:
        print("\n=======================================================")
        print(" EXECUTING ALL ACTIVE PROFILES (SDE & QA)")
        print("=======================================================")
        run_single_profile("sde", config)
        run_single_profile("qa", config)
    else:
        run_single_profile(args.profile, config)

if __name__ == "__main__":
    main()
