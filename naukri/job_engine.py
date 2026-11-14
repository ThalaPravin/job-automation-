import os
import sys
import csv
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except Exception:
            pass

from playwright.sync_api import Page, BrowserContext
from browser_manager import human_sleep
from database import (
    is_job_processed,
    record_job,
    get_today_direct_apply_count,
    get_today_external_count
)

def init_external_csv(csv_path: str = "data/external_jobs.csv"):
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
):
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

def is_strict_software_role(title: str, profile_key: str = "sde") -> bool:
    """
    Enforces strict role filtering to ensure only pure software engineering
    or QA positions are processed, rejecting non-tech or non-software jobs.
    """
    t = title.lower()

    # Hard blacklist for non-SDE / non-technical professions
    hard_excludes = [
        "physiotherapist", "technician", "field", "mechanical", "civil", "electrical", 
        "chemical", "insurance", "sales", "marketing", "telecaller", "bpo", "voice", 
        "nurse", "medical", "clinic", "hardware", "desktop support", "l1 monitoring", 
        "network support", "accountant", "officer", "relationship manager", "recruiter", 
        "hr", "data entry", "content writer", "store manager", "trainee engineer",
        "operations", "branch manager", "audit", "counselor", "telecalling", "associate analyst"
    ]
    if any(ex in t for ex in hard_excludes):
        return False

    if profile_key == "qa":
        qa_includes = [
            "qa", "test", "testing", "quality", "sdet", "automation", "selenium", 
            "cypress", "validation", "sqa"
        ]
        return any(inc in t for inc in qa_includes)
    else:
        sde_includes = [
            "developer", "programmer", "software engineer", "software dev", "backend", 
            "back-end", "java", "full stack", "fullstack", "sde", "frontend", "front-end", 
            "front end", "web developer", "python developer", "golang", "spring", 
            "microservices", "api developer", ".net developer", "c++ developer", 
            "devops engineer", "cloud engineer", "software architect", "coder", "software"
        ]
        return any(inc in t for inc in sde_includes)

def answer_questionnaire(page: Page, screening_answers: Dict[str, Any]) -> bool:
    """
    Handles both modern Naukri chatbot screening drawers
    (div.chatbot_MessageContainer / div.textArea[contenteditable='true'])
    and classic modal screening forms.
    """
    try:
        # 1. Check for Modern Naukri Chatbot Drawer
        chat_box = page.locator("div.textArea[contenteditable='true'], div[data-placeholder*='Type message' i]").first
        if chat_box.is_visible(timeout=3000):
            print("  [*] Chatbot screening drawer detected. Answering questions...")
            for q_idx in range(8):
                if not chat_box.is_visible(timeout=2000):
                    break

                # Extract last bot question text to provide intelligent answers
                bot_text = page.evaluate("""() => {
                    const msgs = Array.from(document.querySelectorAll('.chatbot_MessageContainer li, .botItem, .botMsg'))
                        .map(m => m.innerText.trim()).filter(Boolean);
                    return msgs.length > 0 ? msgs[msgs.length - 1].toLowerCase() : '';
                }""")

                # Determine best answer based on question content
                answer = "Yes"
                if "notice" in bot_text:
                    answer = str(screening_answers.get("notice_period_days", "15"))
                elif "experience" in bot_text and ("how many" in bot_text or "total" in bot_text or "year" in bot_text):
                    answer = str(screening_answers.get("total_experience_years", "1.5"))
                elif "current ctc" in bot_text or "current salary" in bot_text:
                    answer = str(screening_answers.get("current_ctc_lpa", "9"))
                elif "expected ctc" in bot_text or "expected salary" in bot_text:
                    answer = str(screening_answers.get("expected_ctc_lpa", "14"))

                chat_box.click()
                human_sleep(0.3, 0.6)
                chat_box.press_sequentially(answer, delay=50)
                human_sleep(0.2, 0.4)
                chat_box.press("Enter")
                human_sleep(2.0, 3.0)

            # Click Save/Apply in chatbot drawer if present
            save_chat = page.locator(".chatbot_SaveButton, .save-btn, button:has-text('Save'), button:has-text('Submit')").first
            if save_chat.is_visible(timeout=2000) and not save_chat.is_disabled():
                save_chat.click()
                human_sleep(2.0, 3.0)
            return True

        # 2. Check for Classic Modal Questions
        modal = page.locator("div.apply-message, div.questionnaire, div.custom-questions, div[role='dialog']").first
        if modal.is_visible(timeout=2000):
            print("  [*] Classic screening questions detected. Answering...")
            exp_inputs = page.locator("input[type='number'], input[placeholder*='experience' i], input[id*='exp' i]")
            for i in range(exp_inputs.count()):
                try:
                    inp = exp_inputs.nth(i)
                    if inp.is_visible():
                        val = str(screening_answers.get("total_experience_years", "1.5"))
                        inp.fill(val)
                        human_sleep(0.5, 1.0)
                except Exception:
                    pass

            yes_radios = page.locator("label:has-text('Yes'), input[value*='yes' i], input[value*='Yes' i]")
            if yes_radios.count() > 0 and yes_radios.first.is_visible():
                yes_radios.first.click()
                human_sleep(0.5, 1.0)

            notice_days = str(screening_answers.get("notice_period_days", "15"))
            notice_options = page.locator(f"label:has-text('{notice_days}'), label:has-text('Immediate'), input[value*='15']")
            if notice_options.count() > 0 and notice_options.first.is_visible():
                notice_options.first.click()
                human_sleep(0.5, 1.0)

            submit_btn = page.locator("button:has-text('Submit'), button:has-text('Apply'), button:has-text('Save')").first
            if submit_btn.is_visible():
                submit_btn.click()
                human_sleep(2, 4)
                return True

    except Exception as e:
        print(f"  [-] Error handling questionnaire: {e}")

    return False

def process_job_card(
    context: BrowserContext,
    job_data: Dict[str, str],
    screening_answers: Dict[str, Any],
    csv_path: str,
    db_path: str,
    direct_limit_reached: bool
) -> Dict[str, Any]:
    job_id = job_data["job_id"]
    job_url = job_data["job_url"]
    title = job_data["title"]
    company = job_data["company"]
    experience = job_data["experience"]
    location = job_data["location"]

    detail_page = context.new_page()
    result = {"status": "SKIPPED", "type": "UNKNOWN"}

    try:
        detail_page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        human_sleep(2, 4)

        external_btn = detail_page.locator(
            "button:has-text('Apply on company site'), a:has-text('Apply on company site'), "
            "button:has-text('Company site'), a:has-text('Apply on website')"
        ).first

        has_external_link = False
        external_url = job_url

        if external_btn.is_visible(timeout=3000):
            has_external_link = True
            href = external_btn.get_attribute("href")
            if href and href.startswith("http"):
                external_url = href

        if has_external_link or direct_limit_reached:
            print(f"  [EXT] External opening: '{title}' at '{company}'")
            save_external_job_to_csv(job_id, title, company, experience, location, job_url, external_url, csv_path)
            record_job(job_id, title, company, experience, location, job_url, "EXTERNAL", "SAVED_TO_CSV", db_path)
            result = {"status": "SAVED_TO_CSV", "type": "EXTERNAL"}
        else:
            direct_btn = detail_page.locator(
                "button.apply-button, button:has-text('Apply'), div.apply-button-container button"
            ).first

            if direct_btn.is_visible(timeout=3000):
                btn_text = direct_btn.inner_text().strip().lower()
                if "applied" in btn_text:
                    print(f"  [*] Already applied previously to '{title}'")
                    record_job(job_id, title, company, experience, location, job_url, "DIRECT", "ALREADY_APPLIED", db_path)
                    result = {"status": "ALREADY_APPLIED", "type": "DIRECT"}
                else:
                    print(f"  [+] Applying directly to '{title}' at '{company}'...")
                    direct_btn.click()
                    human_sleep(2, 3)

                    answer_questionnaire(detail_page, screening_answers)

                    page_content = detail_page.content().lower()
                    if "reached your daily application limit" in page_content or "limit reached" in page_content:
                        print("  [LIMIT] Naukri daily application limit reached!")
                        record_job(job_id, title, company, experience, location, job_url, "DIRECT", "LIMIT_REACHED", db_path)
                        result = {"status": "LIMIT_REACHED", "type": "DIRECT"}
                    else:
                        human_sleep(2, 3)
                        # Explicitly verify that Naukri accepted the application
                        is_verified_applied = detail_page.evaluate("""() => {
                            const btns = Array.from(document.querySelectorAll('button, div[class*="apply"], span[class*="apply"]'))
                                .map(b => b.innerText.trim().toLowerCase());
                            if (btns.some(t => t === 'applied' || t.includes('already applied'))) return true;
                            const body = document.body.innerText.toLowerCase();
                            if (body.includes('application sent') || body.includes('applied successfully') || body.includes('successfully applied')) return true;
                            return false;
                        }""")

                        if is_verified_applied:
                            print(f"  [SUCCESS] ✔ Confirmed applied to '{title}'!")
                            record_job(job_id, title, company, experience, location, job_url, "DIRECT", "APPLIED", db_path)
                            result = {"status": "APPLIED", "type": "DIRECT"}
                        else:
                            print(f"  [-] Application unconfirmed for '{title}' (Chatbot or prompt incomplete).")
                            record_job(job_id, title, company, experience, location, job_url, "DIRECT", "UNCONFIRMED", db_path)
                            result = {"status": "UNCONFIRMED", "type": "DIRECT"}
            else:
                save_external_job_to_csv(job_id, title, company, experience, location, job_url, job_url, csv_path)
                record_job(job_id, title, company, experience, location, job_url, "EXTERNAL", "SAVED_TO_CSV", db_path)
                result = {"status": "SAVED_TO_CSV", "type": "EXTERNAL"}

    except Exception as e:
        print(f"  [-] Error processing job {job_id} ({type(e).__name__}): {e}")
        record_job(job_id, title, company, experience, location, job_url, "UNKNOWN", "ERROR", db_path)
        result = {"status": "ERROR", "type": "UNKNOWN"}
    finally:
        try:
            detail_page.close()
        except Exception:
            pass

    return result

def run_job_discovery(
    context: BrowserContext,
    config: Dict[str, Any],
    profile_key: str = "sde"
) -> Dict[str, int]:
    """
    Searches for target roles across pages, filters duplicates,
    enforces strict software development title validation,
    applies directly up to quota, and exports external openings to CSV.
    """
    profile_cfg = config.get("profiles", {}).get(profile_key, config.get("profile", {}))
    common_cfg = config.get("common", config.get("limits", {}))

    roles = profile_cfg.get("roles", ["Java Developer", "Backend Developer", "Software Developer"])
    exp_min = profile_cfg.get("experience_min", 0)
    exp_max = profile_cfg.get("experience_max", 3)
    freshness = common_cfg.get("freshness_days", 3)
    blacklist = config.get("filters", {}).get("blacklist_keywords", [])
    
    db_path = profile_cfg.get("db_path", f"data/naukri_{profile_key}.db")
    csv_path = profile_cfg.get("external_csv_path", f"data/external_jobs_{profile_key}.csv")
    screening_answers = profile_cfg.get("screening_answers", {})

    daily_total_target = common_cfg.get("daily_total_target", 500)
    max_direct_applies = common_cfg.get("max_direct_applies_per_day", 50)
    
    current_direct_count = get_today_direct_apply_count(db_path)
    current_external_count = get_today_external_count(db_path)
    total_processed_today = current_direct_count + current_external_count
    
    print(f"\n[+] Today's Starting Progress [{profile_key.upper()}]: {current_direct_count}/{max_direct_applies} Direct Applies, {current_external_count} External Saved.")
    print(f"[+] Target Daily Volume: {daily_total_target} total openings.")
    
    direct_limit_hit = (current_direct_count >= max_direct_applies)
    search_page = context.new_page()

    for role in roles:
        if total_processed_today >= daily_total_target:
            print(f"[SUCCESS] Daily goal of {daily_total_target} reached across roles!")
            break

        print("\n" + "=" * 50)
        print(f" SEARCHING [{profile_key.upper()}]: {role} (Experience: {exp_min}-{exp_max} Yrs)")
        print("=" * 50)

        keyword_encoded = quote_plus(role)
        page_num = 1
        empty_pages_count = 0

        while total_processed_today < daily_total_target and page_num <= 25:
            search_url = (
                f"https://www.naukri.com/{role.lower().replace(' ', '-')}-jobs"
                f"?k={keyword_encoded}&experience={exp_min}&experience={exp_max}&jobAge={freshness}&sort=f&pageNo={page_num}"
            )
            print(f"\n[+] Loading Page {page_num} [Sorted by Most Recent]: {search_url}")

            loaded = False
            for retry in range(3):
                try:
                    search_page.goto(search_url, wait_until="domcontentloaded", timeout=40000)
                    human_sleep(3, 5)

                    try:
                        sort_trigger = search_page.locator("span:has-text('Relevance'), #sort-by-dd, div.sort-droparrow").first
                        if sort_trigger.is_visible(timeout=1500):
                            sort_trigger.click()
                            human_sleep(0.5, 1.0)
                            date_option = search_page.locator("li:has-text('Date'), a:has-text('Date'), span:has-text('Date')").first
                            if date_option.is_visible(timeout=1500):
                                date_option.click()
                                human_sleep(2, 3)
                                print("[+] Confirmed Sort by Date (Most Recent First) in UI.")
                    except Exception:
                        pass

                    loaded = True
                    break
                except Exception as e:
                    print(f"[-] Load warning (attempt {retry+1}/3): {e}. Retrying in 4s...")
                    human_sleep(4, 6)

            if not loaded:
                print(f"[-] Page {page_num} unreachable after 3 attempts. Moving to next page...")
                page_num += 1
                continue

            job_cards = search_page.locator(
                "div.srp-jobtuple-wrapper, div.jobTuple, div.cust-job-tuple, article.jobTuple"
            )
            card_count = job_cards.count()
            print(f"[+] Found {card_count} job cards on Page {page_num}")

            if card_count == 0:
                empty_pages_count += 1
                if empty_pages_count >= 2:
                    print("[*] No more jobs found for this role. Moving to next search query.")
                    break
            else:
                empty_pages_count = 0

            for i in range(card_count):
                if total_processed_today >= daily_total_target:
                    break

                try:
                    card = job_cards.nth(i)
                    
                    title_elem = card.locator("a.title, a.job-title").first
                    if not title_elem.is_visible(timeout=2000):
                        continue
                        
                    title = clean_text(title_elem.inner_text())
                    job_url = title_elem.get_attribute("href") or ""
                    
                    if not job_url:
                        continue
                    if not job_url.startswith("http"):
                        job_url = "https://www.naukri.com" + job_url

                    job_id_match = re.search(r"-(\d{6,})(?:\?|$)", job_url)
                    job_id = job_id_match.group(1) if job_id_match else job_url.split("?")[0].split("/")[-1]

                    company = clean_text(card.locator("a.comp-name, span.comp-name").first.inner_text() if card.locator("a.comp-name, span.comp-name").count() > 0 else "Unknown")
                    experience = clean_text(card.locator("span.exp-wrap, span.exp, span.experience").first.inner_text() if card.locator("span.exp-wrap, span.exp, span.experience").count() > 0 else f"{exp_min}-{exp_max} Yrs")
                    location = clean_text(card.locator("span.loc-wrap, span.loc, span.location").first.inner_text() if card.locator("span.loc-wrap, span.loc, span.location").count() > 0 else "India")

                    # 1. Blacklist check
                    combined_text = f"{title} {company}"
                    if contains_blacklist_keywords(combined_text, blacklist):
                        print(f"  [-] Skipped blacklisted: '{title}' at '{company}'")
                        continue

                    # 2. STRICT SOFTWARE DEVELOPMENT ROLE CHECK
                    if not is_strict_software_role(title, profile_key):
                        print(f"  [-] Skipped non-{profile_key.upper()} job: '{title}' at '{company}'")
                        continue

                    # 3. Deduplication check in SQLite database
                    if is_job_processed(job_id, db_path):
                        continue

                    job_data = {
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "experience": experience,
                        "location": location,
                        "job_url": job_url
                    }

                    res = process_job_card(
                        context=context,
                        job_data=job_data,
                        screening_answers=screening_answers,
                        csv_path=csv_path,
                        db_path=db_path,
                        direct_limit_reached=direct_limit_hit
                    )
                    
                    if res["status"] == "APPLIED":
                        current_direct_count += 1
                        total_processed_today += 1
                        if current_direct_count >= max_direct_applies:
                            direct_limit_hit = True
                            print("[LIMIT] Max direct daily applications reached. Switching remaining jobs to CSV capture.")
                    elif res["status"] == "LIMIT_REACHED":
                        direct_limit_hit = True
                        print("[LIMIT] Daily direct limit hit on Naukri. Switching remaining to CSV capture.")
                    elif res["status"] == "SAVED_TO_CSV":
                        current_external_count += 1
                        total_processed_today += 1

                    human_sleep(2, 4)

                except Exception as e:
                    print(f"[-] Error parsing card {i}: {e}")
                    continue

            page_num += 1
            human_sleep(3, 6)

    try:
        search_page.close()
    except Exception:
        pass

    return {
        "direct_applied": current_direct_count,
        "external_saved": current_external_count,
        "total_processed": total_processed_today
    }
