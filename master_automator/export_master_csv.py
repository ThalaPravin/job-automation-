"""
Master Job Applications CSV Exporter
Consolidates all applications and job listings across Naukri, Instahyre, Wellfound, and ATS engines
into one unified master CSV file: all_job_applications.csv.
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_ROOT = BASE_DIR.parent
OUTPUT_CSV = BASE_DIR / "all_job_applications.csv"
DESKTOP_CSV = Path(os.path.expanduser("~")) / "Desktop" / "all_job_applications.csv"

def connect_ro(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        uri = f"file:{path.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True)
    except Exception:
        try:
            return sqlite3.connect(str(path))
        except Exception:
            return None

def export_all() -> Path:
    records: List[Dict[str, Any]] = []
    seen_urls = set()

    # 1. NAUKRI DATABASES (Direct Applications)
    naukri_dbs = [
        ("Naukri (SDE)", PROJECTS_ROOT / "bold-heisenberg" / "data" / "naukri_sde.db"),
        ("Naukri (QA)", PROJECTS_ROOT / "bold-heisenberg" / "data" / "naukri_qa.db"),
        ("Naukri (History)", PROJECTS_ROOT / "bold-heisenberg" / "data" / "naukri_history.db")
    ]
    for source_label, db_path in naukri_dbs:
        conn = connect_ro(db_path)
        if not conn:
            continue
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applied_jobs'")
            if not c.fetchone():
                continue
            c.execute("""
                SELECT job_id, title, company, experience, location, job_url, apply_type, status, created_at 
                FROM applied_jobs
            """)
            for row in c.fetchall():
                url = row[5] or ""
                key = url if url else f"{row[2]}_{row[1]}"
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                records.append({
                    "Platform": source_label,
                    "Job ID": row[0] or "",
                    "Job Title": row[1] or "",
                    "Company": row[2] or "",
                    "Experience": row[3] or "",
                    "Location": row[4] or "",
                    "Application Type": row[6] or "DIRECT",
                    "Status": row[7] or "APPLIED",
                    "Job URL": url,
                    "Date Applied / Recorded": row[8] or ""
                })
        except Exception:
            pass
        finally:
            conn.close()

    # 2. NAUKRI EXTERNAL CSVS
    naukri_csvs = [
        ("Naukri External (SDE)", PROJECTS_ROOT / "bold-heisenberg" / "data" / "external_jobs_sde.csv"),
        ("Naukri External (General)", PROJECTS_ROOT / "bold-heisenberg" / "data" / "external_jobs.csv")
    ]
    for source_label, csv_path in naukri_csvs:
        if not csv_path.exists():
            continue
        try:
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("job_url") or row.get("external_url") or ""
                    key = url if url else f"{row.get('company')}_{row.get('title')}"
                    if key in seen_urls:
                        continue
                    seen_urls.add(key)
                    records.append({
                        "Platform": source_label,
                        "Job ID": row.get("job_id", ""),
                        "Job Title": row.get("title", ""),
                        "Company": row.get("company", ""),
                        "Experience": row.get("experience", ""),
                        "Location": row.get("location", ""),
                        "Application Type": "EXTERNAL_CSV",
                        "Status": "SAVED_FOR_APPLY",
                        "Job URL": url,
                        "Date Applied / Recorded": row.get("date_added", "")
                    })
        except Exception:
            pass

    # 3. INSTAHYRE DATABASES (Direct Applications)
    instahyre_dbs = [
        ("Instahyre (SDE)", PROJECTS_ROOT / "hopeful-turing" / "data" / "instahyre_sde.db"),
        ("Instahyre (QA)", PROJECTS_ROOT / "hopeful-turing" / "data" / "instahyre_qa.db")
    ]
    for source_label, db_path in instahyre_dbs:
        conn = connect_ro(db_path)
        if not conn:
            continue
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applied_jobs'")
            if not c.fetchone():
                continue
            c.execute("""
                SELECT job_id, title, company, experience, location, job_url, apply_type, status, created_at 
                FROM applied_jobs
            """)
            for row in c.fetchall():
                url = row[5] or ""
                key = url if url else f"{row[2]}_{row[1]}"
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                records.append({
                    "Platform": source_label,
                    "Job ID": row[0] or "",
                    "Job Title": row[1] or "",
                    "Company": row[2] or "",
                    "Experience": row[3] or "",
                    "Location": row[4] or "",
                    "Application Type": row[6] or "DIRECT",
                    "Status": row[7] or "APPLIED",
                    "Job URL": url,
                    "Date Applied / Recorded": row[8] or ""
                })
        except Exception:
            pass
        finally:
            conn.close()

    # 4. INSTAHYRE EXTERNAL CSVS
    instahyre_csvs = [
        ("Instahyre External (SDE)", PROJECTS_ROOT / "hopeful-turing" / "data" / "external_jobs_sde.csv"),
        ("Instahyre External (QA)", PROJECTS_ROOT / "hopeful-turing" / "data" / "external_jobs_qa.csv")
    ]
    for source_label, csv_path in instahyre_csvs:
        if not csv_path.exists():
            continue
        try:
            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("job_url") or row.get("external_url") or ""
                    key = url if url else f"{row.get('company')}_{row.get('title')}"
                    if key in seen_urls:
                        continue
                    seen_urls.add(key)
                    records.append({
                        "Platform": source_label,
                        "Job ID": row.get("job_id", ""),
                        "Job Title": row.get("title", ""),
                        "Company": row.get("company", ""),
                        "Experience": row.get("experience", ""),
                        "Location": row.get("location", ""),
                        "Application Type": "EXTERNAL_CSV",
                        "Status": "SAVED_FOR_APPLY",
                        "Job URL": url,
                        "Date Applied / Recorded": row.get("date_added", "")
                    })
        except Exception:
            pass

    # 5. WELLFOUND DATABASE
    wf_db = PROJECTS_ROOT / "jolly-hypatia" / "data" / "applications.db"
    conn = connect_ro(wf_db)
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
            if c.fetchone():
                c.execute("SELECT id, job_key, company_name, job_title, job_url, status, applied_at FROM applications")
                for row in c.fetchall():
                    url = row[4] or ""
                    key = url if url else f"{row[2]}_{row[3]}"
                    if key in seen_urls:
                        continue
                    seen_urls.add(key)
                    records.append({
                        "Platform": "Wellfound (AngelList)",
                        "Job ID": str(row[0]),
                        "Job Title": row[3] or "",
                        "Company": row[2] or "",
                        "Experience": "N/A",
                        "Location": "Remote / Hybrid",
                        "Application Type": "DIRECT_AI_PITCH",
                        "Status": row[5] or "APPLIED",
                        "Job URL": url,
                        "Date Applied / Recorded": row[6] or ""
                    })
        except Exception:
            pass
        finally:
            conn.close()

    # 6. AUTOAPPLY MULTI-ATS DATABASE
    aa_db = PROJECTS_ROOT / "quirky-curie" / "data" / "applications.db"
    conn = connect_ro(aa_db)
    if conn:
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
            if c.fetchone():
                c.execute("SELECT job_id, title, company, location, applied_url, platform, status, applied_date FROM applications")
                for row in c.fetchall():
                    url = row[4] or ""
                    key = url if url else f"{row[2]}_{row[1]}"
                    if key in seen_urls:
                        continue
                    seen_urls.add(key)
                    records.append({
                        "Platform": f"ATS ({row[5]})",
                        "Job ID": str(row[0]),
                        "Job Title": row[1] or "",
                        "Company": row[2] or "",
                        "Experience": "N/A",
                        "Location": row[3] or "",
                        "Application Type": "ATS_AUTO",
                        "Status": row[6] or "APPLIED",
                        "Job URL": url,
                        "Date Applied / Recorded": row[7] or ""
                    })
        except Exception:
            pass
        finally:
            conn.close()

    # Sort records: most recent date first
    records.sort(key=lambda r: str(r.get("Date Applied / Recorded", "")), reverse=True)

    # Write to master CSV
    fields = [
        "Platform", "Job Title", "Company", "Experience", "Location",
        "Application Type", "Status", "Date Applied / Recorded", "Job URL", "Job ID"
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    # Also copy to Desktop for instant convenience
    try:
        with open(DESKTOP_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    except Exception:
        pass

    return OUTPUT_CSV, len(records)

if __name__ == "__main__":
    out_path, total = export_all()
    print(f"✔ Successfully exported {total:,} job applications to:")
    print(f"  1. {out_path}")
    print(f"  2. {DESKTOP_CSV}")
