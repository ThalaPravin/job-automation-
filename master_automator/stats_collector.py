"""
Unified Statistics & Metrics Collector
Aggregates live metrics from Naukri, Instahyre, Wellfound, PetBiz Lead Gen, and AutoApply ATS.
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
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_ROOT = BASE_DIR.parent

def _connect_ro(db_path: Path):
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None
    try:
        uri = f"file:{db_path.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True)
    except Exception:
        try:
            return sqlite3.connect(str(db_path))
        except Exception:
            return None

def get_naukri_stats() -> Dict[str, Any]:
    naukri_dir = PROJECTS_ROOT / "bold-heisenberg"
    today_str = datetime.now().strftime("%Y-%m-%d")
    stats = {
        "today_direct": 0,
        "today_external": 0,
        "lifetime_direct": 0,
        "lifetime_external": 0,
        "total_tracked": 0,
        "profiles": {}
    }

    dbs = {
        "sde": naukri_dir / "data" / "naukri_sde.db",
        "qa": naukri_dir / "data" / "naukri_qa.db",
        "legacy": naukri_dir / "data" / "naukri_history.db"
    }

    for p_name, db_file in dbs.items():
        if not db_file.exists():
            continue
        conn = _connect_ro(db_file)
        if not conn:
            continue
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applied_jobs'")
            if not c.fetchone():
                conn.close()
                continue

            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='DIRECT' AND status='APPLIED' AND date(created_at)=date(?)", (today_str,))
            t_dir = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='EXTERNAL' AND status='SAVED_TO_CSV' AND date(created_at)=date(?)", (today_str,))
            t_ext = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='DIRECT' AND status='APPLIED'")
            l_dir = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='EXTERNAL' AND status='SAVED_TO_CSV'")
            l_ext = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM applied_jobs")
            tot = c.fetchone()[0] or 0

            stats["today_direct"] += t_dir
            stats["today_external"] += t_ext
            stats["lifetime_direct"] += l_dir
            stats["lifetime_external"] += l_ext
            stats["total_tracked"] += tot

            stats["profiles"][p_name] = {
                "today_direct": t_dir,
                "today_external": t_ext,
                "lifetime_direct": l_dir,
                "lifetime_external": l_ext,
                "total": tot
            }
        except Exception:
            pass
        finally:
            conn.close()

    return stats

def get_instahyre_stats() -> Dict[str, Any]:
    instahyre_dir = PROJECTS_ROOT / "hopeful-turing"
    today_str = datetime.now().strftime("%Y-%m-%d")
    stats = {
        "today_direct": 0,
        "today_external": 0,
        "lifetime_direct": 0,
        "lifetime_external": 0,
        "total_tracked": 0,
        "profiles": {}
    }

    dbs = {
        "sde": instahyre_dir / "data" / "instahyre_sde.db",
        "qa": instahyre_dir / "data" / "instahyre_qa.db"
    }

    for p_name, db_file in dbs.items():
        if not db_file.exists():
            continue
        conn = _connect_ro(db_file)
        if not conn:
            continue
        try:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applied_jobs'")
            if not c.fetchone():
                conn.close()
                continue

            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='DIRECT' AND status='APPLIED' AND date(created_at)=date(?)", (today_str,))
            t_dir = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='EXTERNAL' AND status='SAVED_TO_CSV' AND date(created_at)=date(?)", (today_str,))
            t_ext = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='DIRECT' AND status='APPLIED'")
            l_dir = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type='EXTERNAL' AND status='SAVED_TO_CSV'")
            l_ext = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM applied_jobs")
            tot = c.fetchone()[0] or 0

            stats["today_direct"] += t_dir
            stats["today_external"] += t_ext
            stats["lifetime_direct"] += l_dir
            stats["lifetime_external"] += l_ext
            stats["total_tracked"] += tot

            stats["profiles"][p_name] = {
                "today_direct": t_dir,
                "today_external": t_ext,
                "lifetime_direct": l_dir,
                "lifetime_external": l_ext,
                "total": tot
            }
        except Exception:
            pass
        finally:
            conn.close()

    return stats

def get_wellfound_stats() -> Dict[str, Any]:
    wf_dir = PROJECTS_ROOT / "jolly-hypatia"
    db_file = wf_dir / "data" / "applications.db"
    today_str = datetime.now().strftime("%Y-%m-%d")
    stats = {
        "today_applied": 0,
        "lifetime_applied": 0,
        "dry_run": 0,
        "total_tracked": 0,
        "recent_applications": []
    }

    if not db_file.exists():
        return stats

    conn = _connect_ro(db_file)
    if not conn:
        return stats

    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
        if not c.fetchone():
            return stats

        c.execute("SELECT COUNT(*) FROM applications WHERE status='APPLIED' AND date(applied_at)=date(?)", (today_str,))
        stats["today_applied"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications WHERE status='APPLIED'")
        stats["lifetime_applied"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications WHERE status='DRY_RUN'")
        stats["dry_run"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications")
        stats["total_tracked"] = c.fetchone()[0] or 0

        c.execute("SELECT company_name, job_title, status, applied_at FROM applications ORDER BY applied_at DESC LIMIT 5")
        for row in c.fetchall():
            stats["recent_applications"].append({
                "company": row[0],
                "title": row[1],
                "status": row[2],
                "date": row[3]
            })
    except Exception:
        pass
    finally:
        conn.close()

    return stats

def get_petbiz_stats() -> Dict[str, Any]:
    pb_dir = PROJECTS_ROOT / "adventurous-goodall"
    db_file = pb_dir / "data" / "pet_leads.db"
    today_str = datetime.now().strftime("%Y-%m-%d")
    stats = {
        "total_leads": 0,
        "with_email": 0,
        "emailed_leads": 0,
        "replied_leads": 0,
        "followups_due": 0
    }

    if not db_file.exists():
        return stats

    conn = _connect_ro(db_file)
    if not conn:
        return stats

    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        if not c.fetchone():
            return stats

        c.execute("SELECT COUNT(*) FROM leads")
        stats["total_leads"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM leads WHERE email IS NOT NULL AND trim(email) != ''")
        stats["with_email"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM leads WHERE status IN ('EMAIL_SENT', 'FOLLOW_UP_1_SENT', 'FOLLOW_UP_2_SENT', 'REPLIED')")
        stats["emailed_leads"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM leads WHERE status='REPLIED'")
        stats["replied_leads"] = c.fetchone()[0] or 0

        c.execute("""
            SELECT COUNT(*) FROM leads 
            WHERE status IN ('EMAIL_SENT', 'FOLLOW_UP_1_SENT') 
              AND next_followup_due IS NOT NULL 
              AND date(next_followup_due) <= date(?)
        """, (today_str,))
        stats["followups_due"] = c.fetchone()[0] or 0
    except Exception:
        pass
    finally:
        conn.close()

    return stats

def get_autoapply_stats() -> Dict[str, Any]:
    aa_dir = PROJECTS_ROOT / "quirky-curie"
    db_file = aa_dir / "data" / "applications.db"
    stats = {
        "applied": 0,
        "manual_review": 0,
        "skipped": 0,
        "total": 0
    }

    if not db_file.exists():
        return stats

    conn = _connect_ro(db_file)
    if not conn:
        return stats

    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
        if not c.fetchone():
            return stats

        c.execute("SELECT COUNT(*) FROM applications WHERE status='APPLIED'")
        stats["applied"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications WHERE status='MANUAL_REVIEW'")
        stats["manual_review"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications WHERE status='SKIPPED'")
        stats["skipped"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications")
        stats["total"] = c.fetchone()[0] or 0
    except Exception:
        pass
    finally:
        conn.close()

    return stats

def get_all_stats() -> Dict[str, Any]:
    naukri = get_naukri_stats()
    instahyre = get_instahyre_stats()
    wellfound = get_wellfound_stats()
    petbiz = get_petbiz_stats()
    autoapply = get_autoapply_stats()

    today_job_apps = (
        naukri["today_direct"] +
        instahyre["today_direct"] +
        wellfound["today_applied"]
    )

    lifetime_job_apps = (
        naukri["lifetime_direct"] +
        instahyre["lifetime_direct"] +
        wellfound["lifetime_applied"] +
        autoapply["applied"]
    )

    today_external_saved = (
        naukri["today_external"] +
        instahyre["today_external"]
    )

    lifetime_external_saved = (
        naukri["lifetime_external"] +
        instahyre["lifetime_external"]
    )

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "aggregate": {
            "today_job_applications": today_job_apps,
            "today_external_saved": today_external_saved,
            "lifetime_job_applications": lifetime_job_apps,
            "lifetime_external_saved": lifetime_external_saved,
            "total_client_leads": petbiz["total_leads"],
            "leads_with_email": petbiz["with_email"],
            "clients_contacted": petbiz["emailed_leads"],
            "client_followups_due": petbiz["followups_due"]
        },
        "platforms": {
            "naukri": naukri,
            "instahyre": instahyre,
            "wellfound": wellfound,
            "petbiz": petbiz,
            "autoapply": autoapply
        }
    }

def print_summary():
    data = get_all_stats()
    agg = data["aggregate"]
    p = data["platforms"]

    print("\n" + "=" * 70)
    print("      🚀 MASTER AUTOMATION CONTROL CENTER - CONSOLIDATED METRICS")
    print(f"      Report Generated: {data['timestamp']}")
    print("=" * 70)

    print("\n[🎯 TODAY'S EXECUTIVE HIGHLIGHTS]")
    print(f"  • Direct Job Applications Sent Today : {agg['today_job_applications']:,}")
    print(f"  • External Career Jobs Saved to CSV   : {agg['today_external_saved']:,}")
    print(f"  • Client Follow-ups Due Today        : {agg['client_followups_due']:,}")

    print("\n[🏆 LIFETIME IMPACT & REACH]")
    print(f"  • Total Direct Job Applications      : {agg['lifetime_job_applications']:,}")
    print(f"  • Total External Sourced Openings    : {agg['lifetime_external_saved']:,}")
    print(f"  • Total Pet Businesses Discovered   : {agg['total_client_leads']:,}")
    print(f"  • Businesses with Verified Emails   : {agg['leads_with_email']:,}")
    print(f"  • Cold Outreach Emails Dispatched   : {agg['clients_contacted']:,}")

    print("\n" + "-" * 70)
    print(" PLATFORM BREAKDOWN:")
    print("-" * 70)

    # Naukri
    nk = p["naukri"]
    print(f" 1. Naukri.com Booster & Apply:")
    print(f"    - Today Direct: {nk['today_direct']} | Today External CSV: {nk['today_external']}")
    print(f"    - Lifetime Direct: {nk['lifetime_direct']} | Lifetime External CSV: {nk['lifetime_external']}")

    # Instahyre
    ih = p["instahyre"]
    print(f" 2. Instahyre Booster & Apply:")
    print(f"    - Today Direct: {ih['today_direct']} | Today External CSV: {ih['today_external']}")
    print(f"    - Lifetime Direct: {ih['lifetime_direct']} | Lifetime External CSV: {ih['lifetime_external']}")

    # Wellfound
    wf = p["wellfound"]
    print(f" 3. Wellfound (AngelList) AI Applier:")
    print(f"    - Today Applied: {wf['today_applied']} | Lifetime Applied: {wf['lifetime_applied']} | Total Tracked: {wf['total_tracked']}")

    # PetBiz
    pb = p["petbiz"]
    print(f" 4. PetBiz Lead Finder & Outreach:")
    print(f"    - Total Leads: {pb['total_leads']} | With Email: {pb['with_email']} | Contacted: {pb['emailed_leads']} | Follow-ups Due: {pb['followups_due']}")

    # AutoApply
    aa = p["autoapply"]
    print(f" 5. AutoApply Multi-ATS Engine:")
    print(f"    - Applied: {aa['applied']} | Review: {aa['manual_review']} | Skipped: {aa['skipped']} | Total: {aa['total']}")

    print("=" * 70 + "\n")

if __name__ == "__main__":
    print_summary()
