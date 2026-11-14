"""
Unified Job Automation Suite - Master Entrypoint
Supported Platforms: Wellfound, Naukri, Instahyre
"""

import argparse
import os
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(
        description="Unified Job Application Automation Suite (Wellfound, Naukri, Instahyre)",
        add_help=False
    )
    parser.add_argument("--platform", choices=["wellfound", "naukri", "instahyre", "all"], default=None, help="Target platform to run")
    parser.add_argument("--wellfound", action="store_true", help="Run Wellfound automation")
    parser.add_argument("--naukri", action="store_true", help="Run Naukri automation")
    parser.add_argument("--instahyre", action="store_true", help="Run Instahyre automation")
    parser.add_argument("--all", action="store_true", help="Run all 3 platforms sequentially")
    parser.add_argument("--dashboard", action="store_true", help="Launch Master Web Dashboard (localhost:8888)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")

    args, remaining = parser.parse_known_args()

    py_cmd = sys.executable
    root_dir = os.path.dirname(os.path.abspath(__file__))

    if args.help:
        parser.print_help()
        print("\n--- Platform Specific Options ---")
        print("  Wellfound : python main.py --wellfound [--apply | --dry-run | --login | --stats] [--limit N]")
        print("  Naukri    : python main.py --naukri [--profile sde|qa | --all]")
        print("  Instahyre : python main.py --instahyre [--profile sde|qa | --all]")
        print("  Master UI : python main.py --dashboard")
        print("  Run All   : python main.py --all")
        return

    # 1. Master Web Dashboard
    if args.dashboard:
        target_dir = os.path.join(root_dir, "master_automator")
        subprocess.run([py_cmd, "web_server.py"], cwd=target_dir)
        return

    # 2. Run All Platforms
    if args.all:
        target_dir = os.path.join(root_dir, "master_automator")
        subprocess.run([py_cmd, "master_cli.py", "--daily"], cwd=target_dir)
        return

    # 3. Naukri Platform
    if args.naukri or args.platform == "naukri":
        target_dir = os.path.join(root_dir, "naukri")
        cmd = [py_cmd, "main.py"] + [a for a in sys.argv[1:] if a not in ["--naukri", "--platform", "naukri"]]
        if not any(c in cmd for c in ["--profile", "--all", "-h", "--help"]):
            cmd.append("--all")
        subprocess.run(cmd, cwd=target_dir)
        return

    # 4. Instahyre Platform
    if args.instahyre or args.platform == "instahyre":
        target_dir = os.path.join(root_dir, "instahyre")
        cmd = [py_cmd, "main.py"] + [a for a in sys.argv[1:] if a not in ["--instahyre", "--platform", "instahyre"]]
        if not any(c in cmd for c in ["--profile", "--all", "-h", "--help"]):
            cmd.append("--all")
        subprocess.run(cmd, cwd=target_dir)
        return

    # 5. Default / Wellfound Platform
    target_dir = os.path.join(root_dir, "wellfound")
    cmd = [py_cmd, "main.py"] + [a for a in sys.argv[1:] if a not in ["--wellfound", "--platform", "wellfound"]]
    subprocess.run(cmd, cwd=target_dir)

if __name__ == "__main__":
    main()
