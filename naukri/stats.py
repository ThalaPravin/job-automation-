"""
Naukri Automation Live Statistics Viewer
Displays real-time breakdown of:
- Direct In-Platform Applications on Naukri
- External Job Openings saved to CSV
- Today's counts vs All-Time Lifetime counts
"""

import os
import sqlite3
import csv
from datetime import datetime

def format_count(n: int) -> str:
    return f"{n:,}"

def display_stats_for_db(db_path: str, title: str):
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check if applied_jobs table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applied_jobs'")
    if not c.fetchone():
        conn.close()
        return

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Today's counts
    c.execute("""
        SELECT COUNT(*) FROM applied_jobs 
        WHERE apply_type = 'DIRECT' AND status = 'APPLIED' AND date(created_at) = date(?)
    """, (today_date,))
    today_direct = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM applied_jobs 
        WHERE apply_type = 'EXTERNAL' AND status = 'SAVED_TO_CSV' AND date(created_at) = date(?)
    """, (today_date,))
    today_external = c.fetchone()[0]

    today_total = today_direct + today_external

    # Lifetime counts
    c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type = 'DIRECT' AND status = 'APPLIED'")
    total_direct = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type = 'EXTERNAL' AND status = 'SAVED_TO_CSV'")
    total_external = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applied_jobs WHERE status = 'ALREADY_APPLIED'")
    total_already = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applied_jobs")
    total_tracked = c.fetchone()[0]

    # Profile events
    c.execute("SELECT action, status, message, created_at FROM profile_events ORDER BY id DESC LIMIT 3")
    recent_events = c.fetchall()

    conn.close()

    print("\n" + "=" * 62)
    print(f" {title.upper()} - LIVE APPLICATION METRICS")
    print("=" * 62)
    print(f" Report Generated : {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f" Database Location: {db_path}")
    print("-" * 62)
    print(f" TODAY'S PROGRESS ({today_date}):")
    print(f"   [1] Direct In-Platform Applied (Naukri) : {today_direct}")
    print(f"   [2] External Links Exported to CSV      : {today_external}")
    print(f"   ---------------------------------------------")
    print(f"   Total Opportunities Captured Today      : {today_total}")
    print("-" * 62)
    print(f" ALL-TIME LIFETIME STATS:")
    print(f"   [*] Total In-Platform Direct Applied    : {total_direct}")
    print(f"   [*] Total External Opportunities Saved  : {total_external}")
    print(f"   [*] Previously Applied Jobs Skipped     : {total_already}")
    print(f"   [*] Total Unique Job Postings Tracked   : {total_tracked}")
    print("-" * 62)
    
    if recent_events:
        print(" RECENT PROFILE UPDATES:")
        for ev in recent_events:
            print(f"   • [{ev[3][:16]}] {ev[0]}: {ev[1]} ({ev[2]})")
        print("=" * 62)

def count_csv_lines(csv_path: str) -> int:
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # Skip header
            return sum(1 for row in reader if row)
        except StopIteration:
            return 0

def main():
    print("\n" + "#" * 62)
    print(" NAUKRI JOB AUTOMATION - COMPREHENSIVE STATS DASHBOARD")
    print("#" * 62)

    found_any = False
    databases = [
        ("data/naukri_history.db", "SDE / Main Account"),
        ("data/naukri_sde.db", "SDE Account"),
        ("data/naukri_qa.db", "QA / SDET Account")
    ]

    for db_path, label in databases:
        if os.path.exists(db_path):
            display_stats_for_db(db_path, label)
            found_any = True

    print("\n" + "=" * 62)
    print(" CSV EXPORT FILE STATUS:")
    print("=" * 62)
    csv_files = [
        ("data/external_jobs.csv", "Main External CSV"),
        ("data/external_jobs_sde.csv", "SDE External CSV"),
        ("data/external_jobs_qa.csv", "QA External CSV")
    ]
    for csv_path, label in csv_files:
        if os.path.exists(csv_path):
            count = count_csv_lines(csv_path)
            print(f" • {label:<22}: {count:>4} active jobs ({csv_path})")

    print("=" * 62 + "\n")

if __name__ == "__main__":
    main()
