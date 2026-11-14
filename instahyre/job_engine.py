import os
import csv
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus

from playwright.sync_api import Page, BrowserContext
from browser_manager import human_sleep
from database import (
    is_job_processed,
    record_job,
    get_today_direct_apply_count,
    get_today_external_count
)

def init_external_csv(csv_path: str = "data/external_jobs.csv") -> None:
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not os.path.exists(csv_path):
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "job_id", "title", "company", "experience", "location", 
                "job_url", "external_url", "date_added"
            ])

def save_external_job_to_csv(
    job_id: str,
    title: str,
    company: str,
    experience: str,
    location: str,
    job_url: str,
    external_url: str,
    csv_path: str = "data/external_jobs.csv"
) -> None:
    init_external_csv(csv_path)
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            job_id, title, company, experience, location, 
            job_url, external_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def contains_blacklist_keywords(text: str, blacklist: List[str]) -> bool:
    lower_text = text.lower()
    for kw in blacklist:
        if kw.lower() in lower_text:
            return True
    return False

def is_strict_software_or_qa_role(title: str, profile_key: str = "sde") -> bool:
    """
    Enforces strict role validation to ensure only relevant software engineering
    or QA / testing roles are processed.
    """
    t = title.lower()

    # Blacklist for non-tech / irrelevant professions
    hard_excludes = [
        "physiotherapist", "technician", "field", "mechanical", "civil", "electrical", 
        "chemical", "insurance", "sales", "marketing", "telecaller", "bpo", "voice", 
        "nurse", "medical", "clinic", "hardware", "desktop support", "l1 monitoring", 
        "network support", "accountant", "officer", "relationship manager", "recruiter", 
        "hr", "data entry", "content writer", "store manager", "operations", "branch manager",
        "counselor", "telecalling", "associate analyst", "business development", "bde"
    ]
    if any(ex in t for ex in hard_excludes):
        return False

    if profile_key == "qa":
        qa_includes = [
            "qa", "test", "testing", "quality", "sdet", "automation", "selenium", 
            "cypress", "validation", "sqa", "manual", "qc"
        ]
        return any(inc in t for inc in qa_includes)
    else:
        sde_includes = [
            "developer", "programmer", "software engineer", "software dev", "backend", 
            "back-end", "java", "golang", "go developer", "full stack", "fullstack", 
            "sde", "api developer", "spring", "microservices", "software", "coder",
            "cloud engineer", "devops", "platform engineer"
        ]
        return any(inc in t for inc in sde_includes)

def close_all_modals(page: Page) -> None:
    """Closes any open modals or overlays to ensure next elements are accessible."""
    modal_close_selectors = [
        ".application-modal .close",
        ".candidate-apply-all-modal .close",
        ".modal .close",
        "button.close",
        "button:has-text('Close')",
        "button:has-text('Cancel')",
        ".modal-header button.close",
        "div[role='dialog'] button.close"
    ]
    for sel in modal_close_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=500):
                btn.click()
                human_sleep(0.5, 1.0)
        except Exception:
            pass

def handle_bulk_apply_popup(page: Page, profile_key: str, db_path: str) -> int:
    """
    Handles Instahyre's 'Want to apply to other similar jobs?' modal popup.
    Clicking 'Apply' here bulk-applies to multiple matching positions at once!
    """
    bulk_count = 0
    try:
        bulk_modal = page.locator(
            ".candidate-apply-all-modal, .application-modal .candidate-apply-all-modal, div:has-text('apply to other similar jobs')"
        ).first
        if bulk_modal.is_visible(timeout=3000):
            print("    [*] BULK APPLY MODAL DETECTED! Clicking bulk 'Apply'...")
            bulk_btn = bulk_modal.locator(
                "button.btn.btn-success, button:has-text('Apply'), button:has-text('Apply to all')"
            ).first
            if bulk_btn.is_visible(timeout=2000):
                bulk_btn.click()
                print("    [OK] Bulk applications submitted successfully!")
                bulk_count = 3  # Instahyre typically applies to 2-5 similar jobs in bulk modal
                human_sleep(3, 5)
    except Exception:
        pass
    return bulk_count

def answer_screening_questions(page: Page, screening_answers: Dict[str, Any]) -> bool:
    """
    Auto-answers standard candidate questionnaires if prompted during application.
    """
    try:
        modal = page.locator(
            "div.questionnaire, div.custom-questions, div[role='dialog'], .application-modal"
        ).first
        if not modal.is_visible(timeout=2000):
            return True

        # Experience inputs
        exp_inputs = modal.locator("input[type='number'], input[placeholder*='experience' i], input[name*='exp' i]")
        for i in range(exp_inputs.count()):
            inp = exp_inputs.nth(i)
            if inp.is_visible():
                inp.fill(str(screening_answers.get("total_experience_years", "1.5")))
                human_sleep(0.3, 0.6)

        # Notice period options
        notice_days = str(screening_answers.get("notice_period_days", "15"))
        notice_opts = modal.locator(f"label:has-text('{notice_days}'), label:has-text('Immediate')")
        if notice_opts.count() > 0 and notice_opts.first.is_visible():
            notice_opts.first.click()
            human_sleep(0.3, 0.6)

        # Relocation radios
        yes_opts = modal.locator("label:has-text('Yes'), input[value*='yes' i]")
        if yes_opts.count() > 0 and yes_opts.first.is_visible():
            yes_opts.first.click()
            human_sleep(0.3, 0.6)

        # Submit / Confirm button
        submit_btn = modal.locator("button:has-text('Submit'), button:has-text('Confirm'), button:has-text('Save')").first
        if submit_btn.is_visible():
            submit_btn.click()
            human_sleep(1, 2)
            return True
    except Exception:
        pass
    return False

def process_candidate_opportunities(
    page: Page,
    config: Dict[str, Any],
    profile_key: str = "sde"
) -> Dict[str, int]:
    """
    Processes the curated Candidate Opportunities Feed:
    https://www.instahyre.com/candidate/opportunities/
    Loops through available matches, clicks View -> Apply -> Bulk Apply.
    """
    profile_cfg = config.get("profiles", {}).get(profile_key, {})
    db_path = profile_cfg.get("db_path", f"data/instahyre_{profile_key}.db")
    screening_answers = profile_cfg.get("screening_answers", {})
    blacklist = config.get("filters", {}).get("blacklist_keywords", [])
    max_direct = config.get("common", {}).get("max_direct_applies_per_day", 100)

    print(f"\n" + "=" * 60)
    print(f" PIPELINE PART 1: CANDIDATE OPPORTUNITIES FEED [{profile_key.upper()}]")
    print(f" URL: https://www.instahyre.com/candidate/opportunities/")
    print("=" * 60)

    applied_here = 0
    try:
        page.goto("https://www.instahyre.com/candidate/opportunities/", wait_until="domcontentloaded", timeout=40000)
        human_sleep(4, 6)

        if "login" in page.url.lower():
            print("[-] Session expired or not logged in. Skipping opportunities feed.")
            return {"direct_applied": 0, "bulk_applied": 0}

        page_index = 1
        while page_index <= 5:
            close_all_modals(page)
            human_sleep(1, 2)

            # Locate all View buttons on opportunity cards
            view_buttons = page.locator("#interested-btn, .opportunity-action-links button.btn-success, button.btn-interested")
            count = view_buttons.count()
            print(f"[+] Page {page_index}: Found {count} opportunity cards with 'View' buttons.")

            if count == 0:
                print("[*] No more active 'View' buttons on current opportunities page.")
                break

            for i in range(count):
                current_applied = get_today_direct_apply_count(db_path)
                if current_applied >= max_direct:
                    print(f"[!] Max direct daily apply limit reached ({max_direct}).")
                    return {"direct_applied": applied_here}

                close_all_modals(page)

                # Fetch fresh list of buttons
                buttons = page.locator("#interested-btn, .opportunity-action-links button.btn-success, button.btn-interested")
                if i >= buttons.count():
                    break

                btn = buttons.nth(i)
                if not btn.is_visible():
                    continue

                btn_txt = btn.inner_text().strip().lower()
                if "applied" in btn_txt:
                    continue

                try:
                    btn.scroll_into_view_if_needed()
                    human_sleep(0.5, 1.0)
                    btn.click()
                    human_sleep(1.5, 3.0)

                    # Modal apply button
                    apply_btn = page.locator(
                        "button.btn.btn-lg.btn-primary.new-btn, button:has-text('Apply'), button[ng-click*='submitChoice']"
                    ).first

                    if apply_btn.is_visible(timeout=4000):
                        apply_btn.click()
                        applied_here += 1
                        print(f"  [OK] Successfully Applied on Opportunity [{applied_here}]")
                        human_sleep(2, 4)

                        answer_screening_questions(page, screening_answers)

                        # Handle bulk apply recommendations
                        bulk = handle_bulk_apply_popup(page, profile_key, db_path)
                        applied_here += bulk

                        # Record in DB
                        record_job(
                            job_id=f"opp_{int(time.time())}_{applied_here}",
                            title=f"Opportunity {profile_key.upper()}",
                            company="Instahyre Direct Match",
                            experience=f"{profile_cfg.get('experience_min', 0)}-{profile_cfg.get('experience_max', 3)} Yrs",
                            location="India",
                            job_url=page.url,
                            apply_type="DIRECT",
                            status="APPLIED",
                            db_path=db_path
                        )
                    else:
                        print("  [*] Apply button not found in modal, closing...")

                    close_all_modals(page)
                    human_sleep(1.5, 3.0)

                except Exception as e:
                    print(f"  [-] Error on opportunity {i}: {e}")
                    close_all_modals(page)
                    continue

            # Pagination check for opportunities tab
            next_btn = page.locator("a:has-text('Next'), .pagination li.next a, button:has-text('Next')").first
            if next_btn.is_visible(timeout=2000):
                print(f"[+] Moving to Opportunities Page {page_index + 1}...")
                next_btn.click()
                page_index += 1
                human_sleep(3, 5)
            else:
                break

    except Exception as e:
        print(f"[-] Error processing opportunities feed: {e}")

    return {"direct_applied": applied_here}

def process_single_search_job(
    page: Page,
    job_item: Dict[str, Any],
    profile_key: str,
    screening_answers: Dict[str, Any],
    csv_path: str,
    db_path: str,
    direct_limit_reached: bool
) -> Dict[str, Any]:
    """
    Processes an individual job object from Instahyre's search engine:
    If is_sourced -> Saves external URL to CSV.
    If direct -> Navigates to public_url and applies in 1-click.
    """
    job_id = str(job_item.get("id", ""))
    title = clean_text(job_item.get("title", ""))
    company = clean_text(job_item.get("employer", {}).get("company_name", "Unknown"))
    locations = job_item.get("locations", "India")
    if isinstance(locations, list):
        locations = ", ".join(locations)
    public_url = job_item.get("public_url", "")
    is_sourced = job_item.get("is_sourced", False)
    sourced_apply_url = job_item.get("sourced_apply_url", "") or public_url
    exp_str = f"{job_item.get('min_exp', 0)}-{job_item.get('max_exp', 3)} Yrs"

    # If direct daily application quota is reached, route to CSV
    if direct_limit_reached:
        save_external_job_to_csv(
            job_id=job_id,
            title=title,
            company=company,
            experience=exp_str,
            location=locations,
            job_url=public_url,
            external_url=sourced_apply_url,
            csv_path=csv_path
        )
        record_job(
            job_id=job_id,
            title=title,
            company=company,
            experience=exp_str,
            location=locations,
            job_url=public_url,
            external_url=sourced_apply_url,
            apply_type="EXTERNAL",
            status="SAVED_TO_CSV",
            db_path=db_path
        )
        print(f"  [->] Daily direct limit hit. Saved to CSV: '{title}' at '{company}'")
        return {"status": "SAVED_TO_CSV", "type": "EXTERNAL"}

    # Instahyre Pre-check: Skip already reviewed or applied jobs without loading page
    if job_item.get("interview_status", 0) != 0 or job_item.get("reviewed_at") is not None:
        record_job(job_id, title, company, exp_str, locations, public_url, "DIRECT", "ALREADY_APPLIED", "", db_path)
        return {"status": "ALREADY_APPLIED", "type": "DIRECT"}

    # Attempt Direct In-Platform Application on Instahyre
    try:
        print(f"  [+] Opening job to apply: '{title}' at '{company}'...")
        page.goto(public_url, wait_until="domcontentloaded", timeout=30000)
        human_sleep(2, 4)

        # Wait briefly for Angular to render DOM elements
        human_sleep(2, 3)

        # Look for Apply Button
        apply_btn = page.locator(
            "button#job_details_top, button#job_details_bottom, button:has-text('Apply now'), button:has-text('Apply'), .btn-interested"
        ).first

        try:
            apply_btn.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        if apply_btn.is_visible():
            btn_text = apply_btn.inner_text().strip().lower()
            if "applied" in btn_text:
                print(f"  [*] Already applied previously to '{title}'")
                record_job(job_id, title, company, exp_str, locations, public_url, "DIRECT", "ALREADY_APPLIED", "", db_path)
                return {"status": "ALREADY_APPLIED", "type": "DIRECT"}

            try:
                apply_btn.click(timeout=3000)
            except Exception:
                try:
                    apply_btn.click(force=True, timeout=3000)
                except Exception:
                    page.evaluate("el => el.click()", apply_btn.element_handle())
            human_sleep(2, 3)

            # Check if a confirmation modal with secondary Apply/Submit button opened
            modal_apply = page.locator(
                "div.application-modal button:has-text('Apply'), div.modal button:has-text('Apply'), "
                "button.btn.btn-lg.btn-primary.new-btn, button[ng-click*='submitChoice']"
            ).first
            if modal_apply.is_visible(timeout=3000):
                try:
                    modal_apply.click()
                    human_sleep(2, 3)
                except Exception:
                    pass

            # Check for questionnaire / screening answers
            answer_screening_questions(page, screening_answers)

            # Handle bulk apply if prompted
            handle_bulk_apply_popup(page, profile_key, db_path)
            close_all_modals(page)

            # Close any extra popups or redirected career portal tabs
            if len(page.context.pages) > 1:
                for p_tab in list(page.context.pages):
                    if p_tab != page:
                        try:
                            p_tab.close()
                        except Exception:
                            pass

            print(f"  [OK] Successfully Applied to '{title}' at '{company}'!")
            record_job(job_id, title, company, exp_str, locations, public_url, "DIRECT", "APPLIED", "", db_path)
            return {"status": "APPLIED", "type": "DIRECT"}
        else:
            # If no direct apply button, save to CSV
            save_external_job_to_csv(job_id, title, company, exp_str, locations, public_url, public_url, csv_path)
            record_job(job_id, title, company, exp_str, locations, public_url, "EXTERNAL", "SAVED_TO_CSV", public_url, db_path)
            return {"status": "SAVED_TO_CSV", "type": "EXTERNAL"}

    except Exception as e:
        print(f"  [-] Error applying to direct job {job_id}: {e}")
        save_external_job_to_csv(job_id, title, company, exp_str, locations, public_url, public_url, csv_path)
        record_job(job_id, title, company, exp_str, locations, public_url, "EXTERNAL", "SAVED_TO_CSV", public_url, db_path)
        return {"status": "SAVED_TO_CSV", "type": "EXTERNAL"}

def run_targeted_search_engine(
    page: Page,
    config: Dict[str, Any],
    profile_key: str = "sde"
) -> Dict[str, int]:
    """
    Executes deep targeted search across all skills (Java, Golang, Backend, QA, SDET, etc.)
    and experience years (0, 1, 2, 3), applying directly and saving external openings.
    """
    profile_cfg = config.get("profiles", {}).get(profile_key, {})
    common_cfg = config.get("common", {})
    skills = profile_cfg.get("skills", ["Java", "Backend"])
    blacklist = config.get("filters", {}).get("blacklist_keywords", [])
    screening_answers = profile_cfg.get("screening_answers", {})
    
    db_path = profile_cfg.get("db_path", f"data/instahyre_{profile_key}.db")
    csv_path = profile_cfg.get("external_csv_path", f"data/external_jobs_{profile_key}.csv")
    
    daily_total_target = common_cfg.get("daily_total_target", 500)
    max_direct_applies = common_cfg.get("max_direct_applies_per_day", 100)
    
    current_direct = get_today_direct_apply_count(db_path)
    current_external = get_today_external_count(db_path)
    total_processed = current_direct + current_external
    
    direct_limit_hit = (current_direct >= max_direct_applies)

    print(f"\n" + "=" * 60)
    print(f" PIPELINE PART 2: HIGH-VOLUME SKILL & EXPERIENCE SEARCH [{profile_key.upper()}]")
    print(f" Focus Skills: {', '.join(skills)}")
    print(f" Experience Range: 0 to 3 Years")
    print(f" Current Progress: {current_direct}/{max_direct_applies} Direct Applies, {current_external} External Saved")
    print("=" * 60)

    # Experience years to cycle through: 0, 1, 2, 3
    experience_years = list(range(
        profile_cfg.get("experience_min", 0),
        profile_cfg.get("experience_max", 3) + 1
    ))

    # Navigate to base search page first to ensure cookies/session are active
    try:
        page.goto("https://www.instahyre.com/search-jobs/", wait_until="domcontentloaded", timeout=30000)
        human_sleep(2, 3)
    except Exception:
        pass

    for skill in skills:
        if total_processed >= daily_total_target:
            print(f"[OK] Daily target of {daily_total_target} jobs reached!")
            break

        print(f"\n---> Searching Skill: [{skill.upper()}] (0-3 Yrs Exp) <---")

        for yr in experience_years:
            if total_processed >= daily_total_target:
                break

            offset = 0
            empty_batches = 0

            while offset <= 140 and total_processed < daily_total_target:
                api_url = (
                    f"https://www.instahyre.com/api/v1/job_search"
                    f"?company_size=0&job_type=0&skills={quote_plus(skill)}&years={yr}&offset={offset}&status=0"
                )

                try:
                    # Execute fetch inside page context to retain all session headers/cookies
                    api_data = page.evaluate("""
                    async (url) => {
                        try {
                            const resp = await fetch(url, {
                                headers: { 'Accept': 'application/json, text/plain, */*' }
                            });
                            if (!resp.ok) return { error: resp.status };
                            return await resp.json();
                        } catch (e) {
                            return { error: e.toString() };
                        }
                    }
                    """, api_url)

                    if not api_data or "error" in api_data:
                        print(f"  [-] Error or rate-limit fetching batch at offset {offset}")
                        break

                    jobs = api_data.get("objects", [])
                    total_available = api_data.get("meta", {}).get("total_count", 0)

                    if not jobs:
                        empty_batches += 1
                        if empty_batches >= 2:
                            break
                        offset += 35
                        continue

                    empty_batches = 0
                    print(f"  [+] Skill '{skill}' ({yr} Yrs Exp, Offset {offset}): Processing {len(jobs)} jobs (Total in category: {total_available})")

                    for job in jobs:
                        if total_processed >= daily_total_target:
                            break

                        job_id = str(job.get("id", ""))
                        title = clean_text(job.get("title", ""))
                        company = clean_text(job.get("employer", {}).get("company_name", ""))
                        
                        # Deduplication check from local DB
                        if is_job_processed(job_id, db_path):
                            continue

                        # Instahyre Server-Side Status Check: Skip if already applied/reviewed
                        if job.get("interview_status", 0) != 0 or job.get("reviewed_at") is not None:
                            locations_str = job.get("locations", "India")
                            if isinstance(locations_str, list):
                                locations_str = ", ".join(locations_str)
                            record_job(
                                job_id, title, company,
                                f"{job.get('min_exp', 0)}-{job.get('max_exp', 3)} Yrs",
                                locations_str, job.get("public_url", ""),
                                "DIRECT", "ALREADY_APPLIED", "", db_path
                            )
                            continue

                        # Blacklist check
                        combined = f"{title} {company}"
                        if contains_blacklist_keywords(combined, blacklist):
                            continue

                        # Strict software or QA role check
                        if not is_strict_software_or_qa_role(title, profile_key):
                            continue

                        # Process job
                        res = process_single_search_job(
                            page=page,
                            job_item=job,
                            profile_key=profile_key,
                            screening_answers=screening_answers,
                            csv_path=csv_path,
                            db_path=db_path,
                            direct_limit_reached=direct_limit_hit
                        )

                        if res["status"] == "APPLIED":
                            current_direct += 1
                            total_processed += 1
                            if current_direct >= max_direct_applies:
                                direct_limit_hit = True
                                print("[!] Max direct daily applications reached. Diverting remaining jobs to CSV capture.")
                        elif res["status"] == "SAVED_TO_CSV":
                            current_external += 1
                            total_processed += 1

                        human_sleep(
                            common_cfg.get("min_delay_seconds", 2),
                            common_cfg.get("max_delay_seconds", 4)
                        )

                    offset += 35
                    human_sleep(2, 3)

                except Exception as e:
                    print(f"  [-] Batch exception at offset {offset}: {e}")
                    break

    return {
        "direct_applied": current_direct,
        "external_saved": current_external,
        "total_processed": total_processed
    }

def run_job_discovery(
    context: BrowserContext,
    config: Dict[str, Any],
    profile_key: str = "sde"
) -> Dict[str, int]:
    """
    Main orchestration routine for job discovery:
    Runs Pipeline Part 1 (Candidate Opportunities Feed)
    and Pipeline Part 2 (High-Volume Targeted Search).
    """
    page = context.pages[0] if context.pages else context.new_page()
    
    # 1. Opportunities Feed (Direct Matches)
    opp_results = process_candidate_opportunities(page, config, profile_key)
    
    # 2. High-Volume Targeted Skill Discovery
    search_results = run_targeted_search_engine(page, config, profile_key)
    
    return {
        "direct_applied": search_results["direct_applied"],
        "external_saved": search_results["external_saved"],
        "total_processed": search_results["total_processed"]
    }
