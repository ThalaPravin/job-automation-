"""
Master Automation CLI & Interactive Command Center
Naukri • Instahyre • Wellfound • PetBiz Lead Gen • Multi-ATS Engine
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import argparse
import webbrowser
from pathlib import Path

from orchestrator import MasterOrchestrator, load_config
from stats_collector import print_summary, get_all_stats

BANNER = r"""
================================================================================
  ██████╗  ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ 
 ██╔════╝ ██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
 ██║  ███╗██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║
 ██║   ██║██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║
 ╚██████╔╝╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝
  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ 
        UNIFIED JOB & CLIENT AUTOMATION COMMAND CENTER
    Naukri • Instahyre • Wellfound • PetBiz Outreach • Multi-ATS
================================================================================
"""

def print_banner():
    print(BANNER)

def run_naukri_options(orchestrator: MasterOrchestrator):
    print("\n[NAUKRI OPTIONS]")
    print(" 1. Run BOTH SDE & QA Accounts (Recommended Daily)")
    print(" 2. Run SDE Profile Only")
    print(" 3. Run QA / SDET Profile Only")
    print(" 0. Back")
    c = input("\nSelect [1-3, 0]: ").strip()
    if c == "1":
        orchestrator.run_task("naukri", ["-u", "main.py", "--all"])
    elif c == "2":
        orchestrator.run_task("naukri", ["-u", "main.py", "--profile", "sde"])
    elif c == "3":
        orchestrator.run_task("naukri", ["-u", "main.py", "--profile", "qa"])

def run_instahyre_options(orchestrator: MasterOrchestrator):
    print("\n[INSTAHYRE OPTIONS]")
    print(" 1. Run BOTH SDE & QA Accounts (Recommended Daily)")
    print(" 2. Run SDE Profile Only")
    print(" 3. Run QA / SDET Profile Only")
    print(" 0. Back")
    c = input("\nSelect [1-3, 0]: ").strip()
    if c == "1":
        orchestrator.run_task("instahyre", ["-u", "main.py", "--all"])
    elif c == "2":
        orchestrator.run_task("instahyre", ["-u", "main.py", "--profile", "sde"])
    elif c == "3":
        orchestrator.run_task("instahyre", ["-u", "main.py", "--profile", "qa"])

def run_wellfound_options(orchestrator: MasterOrchestrator):
    print("\n[WELLFOUND OPTIONS]")
    print(" 1. Live Apply (10 Applications with AI Pitch Note)")
    print(" 2. Custom Limit Live Apply")
    print(" 3. Dry-Run Mode (Safe Pitch Generation & Screenshot without Submitting)")
    print(" 0. Back")
    c = input("\nSelect [1-3, 0]: ").strip()
    if c == "1":
        orchestrator.run_task("wellfound", ["-u", "main.py", "--apply", "--limit", "10"])
    elif c == "2":
        lim = input("Enter number of applications [e.g. 5, 10, 15]: ").strip() or "10"
        orchestrator.run_task("wellfound", ["-u", "main.py", "--apply", "--limit", lim])
    elif c == "3":
        orchestrator.run_task("wellfound", ["-u", "main.py", "--dry-run", "--limit", "5"])

def run_petbiz_options(orchestrator: MasterOrchestrator):
    print("\n[PETBIZ CLIENT OUTREACH OPTIONS]")
    print(" 1. Send Scheduled Follow-ups that are DUE Today (Recommended Daily)")
    print(" 2. Send Initial Cold Pitch Emails (Batch of 5 leads)")
    print(" 3. Scrape / Discover New Leads from Selected Cities")
    print(" 4. Launch PetBiz Web UI Dashboard (http://localhost:5000)")
    print(" 0. Back")
    c = input("\nSelect [1-4, 0]: ").strip()
    if c == "1":
        orchestrator.run_task("petbiz", ["-u", "cli.py", "followup", "--limit", "10", "--force-real"])
    elif c == "2":
        orchestrator.run_task("petbiz", ["-u", "cli.py", "send", "--limit", "5", "--force-real"])
    elif c == "3":
        cities = input("Enter comma-separated cities [default: Mumbai,Pune,Bengaluru,Delhi]: ").strip()
        if not cities:
            cities = "Mumbai,Pune,Bengaluru,Delhi"
        orchestrator.run_task("petbiz", ["-u", "cli.py", "find", "--cities", cities, "--limit", "10"])
    elif c == "4":
        import subprocess
        pb_dir = orchestrator.projects["petbiz"]["dir"]
        subprocess.Popen(["C:\\Python314\\python.exe", "run.py"], cwd=pb_dir)
        print("PetBiz web app launched at http://localhost:5000")

def run_autoapply_options(orchestrator: MasterOrchestrator):
    print("\n[AUTOAPPLY ATS ENGINE OPTIONS]")
    print(" 1. Run Auto Mode (Apply to Greenhouse, Lever, Ashby up to 10 jobs)")
    print(" 2. Run Review Mode (Walkthrough with confirmation before submitting)")
    print(" 0. Back")
    c = input("\nSelect [1-2, 0]: ").strip()
    if c == "1":
        orchestrator.run_task("autoapply", ["-u", "run_applier.py", "--mode", "auto", "--limit", "10"])
    elif c == "2":
        orchestrator.run_task("autoapply", ["-u", "run_applier.py", "--mode", "review", "--limit", "5"])

def setup_scheduler_interactive():
    from scheduler_manager import register_windows_task, get_task_status
    print("\n[WINDOWS TASK SCHEDULER SETUP]")
    status = get_task_status()
    print(f"Current Status: {status}")
    print("\nThis will register a Windows Scheduled Task to execute all daily automations")
    print("automatically every morning hands-free at 9:00 AM.")
    time_str = input("Enter trigger time [HH:MM, default 09:00]: ").strip() or "09:00"
    success, msg = register_windows_task(time_str)
    if success:
        print(f"\n✔ SUCCESS: {msg}")
    else:
        print(f"\n[-] FAILED: {msg}")

def launch_web_server():
    import subprocess
    base_dir = Path(__file__).resolve().parent
    web_script = base_dir / "web_server.py"
    subprocess.Popen(["C:\\Python314\\python.exe", str(web_script)], cwd=str(base_dir))
    print("\n🌐 Web Control Center launched! Opening browser at http://localhost:8888 ...")
    webbrowser.open("http://localhost:8888")

def interactive_loop():
    orchestrator = MasterOrchestrator()
    while True:
        print_banner()
        print("  MAIN MENU:")
        print("  [1] 🚀 Run ALL Daily Automations (Naukri + Instahyre + Wellfound + PetBiz)")
        print("  [2] 💼 Run Naukri Daily Booster & Auto-Apply (SDE & QA)")
        print("  [3] ⚡ Run Instahyre Daily Booster & Auto-Apply (SDE & QA)")
        print("  [4] 🦄 Run Wellfound AI Pitch & Job Applier")
        print("  [5] 🐾 Run PetBiz Client Lead Generation & Outreach")
        print("  [6] 🎯 Run AutoApply Multi-ATS Engine (Greenhouse / Lever / Ashby)")
        print("  [7] 📊 View Consolidated Analytics & Stats Dashboard")
        print("  [8] 🌐 Launch Web Dashboard (http://localhost:8888)")
        print("  [9] ⏰ Setup Windows Automated Daily Schedule (9:00 AM)")
        print("  [0] Exit")
        print("-" * 80)
        choice = input("Enter your choice [1-9, 0]: ").strip()

        if choice == "1":
            print("\n🚀 Starting Full Daily Automation Sequence...")
            orchestrator.run_daily_suite()
            print_summary()
            input("\nPress [ENTER] to return to menu...")
        elif choice == "2":
            run_naukri_options(orchestrator)
            input("\nPress [ENTER] to return to menu...")
        elif choice == "3":
            run_instahyre_options(orchestrator)
            input("\nPress [ENTER] to return to menu...")
        elif choice == "4":
            run_wellfound_options(orchestrator)
            input("\nPress [ENTER] to return to menu...")
        elif choice == "5":
            run_petbiz_options(orchestrator)
            input("\nPress [ENTER] to return to menu...")
        elif choice == "6":
            run_autoapply_options(orchestrator)
            input("\nPress [ENTER] to return to menu...")
        elif choice == "7":
            print_summary()
            input("\nPress [ENTER] to return to menu...")
        elif choice == "8":
            launch_web_server()
            input("\nPress [ENTER] to return to menu...")
        elif choice == "9":
            setup_scheduler_interactive()
            input("\nPress [ENTER] to return to menu...")
        elif choice == "0":
            print("\nExiting Master Command Center. Goodbye!\n")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

def main():
    parser = argparse.ArgumentParser(description="Master Automation Orchestrator for Jobs & Leads")
    parser.add_argument("--daily", action="store_true", help="Run the full daily routine non-interactively (ideal for scheduler)")
    parser.add_argument("--stats", action="store_true", help="Print aggregated analytics report and exit")
    parser.add_argument("--naukri", action="store_true", help="Run Naukri automation only")
    parser.add_argument("--instahyre", action="store_true", help="Run Instahyre automation only")
    parser.add_argument("--wellfound", action="store_true", help="Run Wellfound automation only")
    parser.add_argument("--petbiz", action="store_true", help="Run PetBiz follow-ups and outreach only")
    parser.add_argument("--autoapply", action="store_true", help="Run AutoApply ATS engine only")
    parser.add_argument("--web", action="store_true", help="Launch the Web Dashboard server")

    args = parser.parse_args()
    orchestrator = MasterOrchestrator()

    if args.stats:
        print_summary()
        return

    if args.web:
        launch_web_server()
        return

    if args.daily:
        print("▶ Executing Daily Automation Suite non-interactively...")
        res = orchestrator.run_daily_suite()
        print_summary()
        sys.exit(0 if res.get("status") == "COMPLETED" else 1)

    if args.naukri:
        orchestrator.run_task("naukri")
        return
    if args.instahyre:
        orchestrator.run_task("instahyre")
        return
    if args.wellfound:
        orchestrator.run_task("wellfound")
        return
    if args.petbiz:
        orchestrator.run_task("petbiz")
        return
    if args.autoapply:
        orchestrator.run_task("autoapply")
        return

    # No arguments passed: enter interactive loop
    try:
        interactive_loop()
    except KeyboardInterrupt:
        print("\n\nSession terminated by user. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
