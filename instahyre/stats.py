"""
Instahyre Job Automation Engine - Metrics & Statistics Dashboard
Displays today's and lifetime progress across both SDE and QA tracks.
"""

import os
import glob
import yaml
from datetime import datetime
from database import (
    get_today_direct_apply_count,
    get_today_external_count,
    get_total_stats
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def count_csv_lines(csv_path: str) -> int:
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        return max(0, len(lines) - 1)  # Minus header

def main():
    print("\n" + "=" * 70)
    print(" INSTAHYRE AUTOMATION DASHBOARD - METRICS & ANALYTICS")
    print(f" Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    config_path = os.path.join(BASE_DIR, "config.yaml")
    if not os.path.exists(config_path):
        print("[-] config.yaml not found.")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    profiles = config.get("profiles", {})
    total_today_direct = 0
    total_today_external = 0
    total_all_time_direct = 0
    total_all_time_external = 0

    for profile_key, pcfg in profiles.items():
        name = pcfg.get("name", profile_key.upper())
        db_path = pcfg.get("db_path", f"data/instahyre_{profile_key}.db")
        csv_path = pcfg.get("external_csv_path", f"data/external_jobs_{profile_key}.csv")

        today_direct = get_today_direct_apply_count(db_path) if os.path.exists(db_path) else 0
        today_ext = get_today_external_count(db_path) if os.path.exists(db_path) else 0
        csv_count = count_csv_lines(csv_path)

        lifetime = get_total_stats(db_path) if os.path.exists(db_path) else {
            "total_direct_applied": 0, "total_external_saved": 0, "total_jobs_tracked": 0
        }

        total_today_direct += today_direct
        total_today_external += today_ext
        total_all_time_direct += lifetime["total_direct_applied"]
        total_all_time_external += lifetime["total_external_saved"]

        print(f"\n[PROFILE: {name.upper()}]")
        print(f"  * Database File                : {db_path} (Exists: {os.path.exists(db_path)})")
        print(f"  * Today's Direct Applications  : {today_direct}")
        print(f"  * Today's External Jobs Saved  : {today_ext}")
        print(f"  * Lifetime Direct Applied      : {lifetime['total_direct_applied']}")
        print(f"  * Lifetime External In CSV     : {lifetime['total_external_saved']} ({csv_count} rows in CSV)")
        print(f"  * Total Jobs Tracked in DB     : {lifetime['total_jobs_tracked']}")
        print(f"  * CSV Export Location          : {os.path.abspath(csv_path)}")

    print("\n" + "-" * 70)
    print(" OVERALL AGGREGATE SUMMARY (ALL PROFILES)")
    print("-" * 70)
    print(f"  * Combined Applications Today   : {total_today_direct}")
    print(f"  * Combined External Jobs Today  : {total_today_external}")
    print(f"  * Total Lifetime Direct Applies : {total_all_time_direct}")
    print(f"  * Total Lifetime External Jobs  : {total_all_time_external}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
