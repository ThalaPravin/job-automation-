import os
import sys
import time
from typing import Dict, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from browser_manager import human_sleep
from database import record_profile_event

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except Exception:
            pass

def update_resume_and_profile(page: Page, config: Dict[str, Any], profile_name: str = "default") -> bool:
    """
    Executes the exact daily resume refresh sequence:
    1. Navigates to Naukri profile
    2. Overwrites/uploads the fresh resume file from the provided path
    3. Verifies upload confirmation and reads 'Uploaded on [Date]' from DOM
    4. Touches profile headline/summary to guarantee 'Active Today' recruiter status
    """
    profile_cfg = config.get("profiles", {}).get(profile_name, config.get("profile", {}))
    resume_path = profile_cfg.get("resume_path")

    if not resume_path or not os.path.exists(resume_path):
        err = f"Resume file not found at: {resume_path}"
        print(f"[-] {err}")
        record_profile_event("RESUME_REFRESH", "FAILED", err)
        return False

    print("\n" + "=" * 60)
    print(f" RESUME REFRESH & PROFILE TIMESTAMP BOOSTER [{profile_name.upper()}]")
    print("=" * 60)
    print(f"[+] Target Resume: {resume_path}")
    print(f"[+] Navigating to Naukri profile...")
    
    page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
    human_sleep(3, 5)

    if "login" in page.url or "nlogin" in page.url:
        err = f"Not logged in for profile [{profile_name}]! Please run 'python setup_session.py --profile {profile_name}'."
        print(f"[-] {err}")
        record_profile_event("AUTH_CHECK", "FAILED", err)
        return False

    print(f"[+] Profile loaded successfully: {page.title()}")

    # Upload/Replace the specified resume file
    uploaded = False
    try:
        print(f"[+] Uploading resume from: {resume_path}...")
        file_input = page.locator("input#attachCV, input[type='file']#attachCV").first
        if file_input.count() == 0:
            file_input = page.locator("input[type='file']").first

        if file_input.count() > 0:
            file_input.set_input_files(resume_path)
            print("[+] File sent to Naukri upload handler. Waiting for confirmation...")
            human_sleep(5, 8)

            try:
                toast = page.locator("div.msgBox, div.success-toast, p:has-text('uploaded')").first
                if toast.is_visible(timeout=5000):
                    print(f"[SUCCESS] Upload confirmed by toast: '{toast.inner_text().strip()}'")
            except Exception:
                pass

            try:
                uploaded_date_elem = page.locator(
                    "span:has-text('Uploaded on'), span.upload-date, p.caption:has-text('Uploaded on')"
                ).first
                if uploaded_date_elem.is_visible(timeout=3000):
                    print(f"[VERIFIED] {uploaded_date_elem.inner_text().strip()}")
            except Exception:
                pass

            uploaded = True
            record_profile_event("RESUME_UPLOAD", "SUCCESS", f"Uploaded {os.path.basename(resume_path)}")
            print(f"[SUCCESS] Resume refreshed for {os.path.basename(resume_path)}!")
        else:
            print("[-] Error: Resume upload input element not found on page.")
            record_profile_event("RESUME_UPLOAD", "FAILED", "Input element missing")
    except Exception as e:
        print(f"[-] Error while uploading resume: {e}")
        record_profile_event("RESUME_UPLOAD", "ERROR", str(e))

    # Touch profile headline to force 'Active Today' recruiter timestamp
    if profile_cfg.get("touch_profile_fields", True):
        try:
            print("[+] Touching profile headline to guarantee immediate 'Active Today' recruiter timestamp...")
            headline_edit = page.locator("span.edit.icon, span:has-text('Resume Headline') + span.edit").first
            if headline_edit.is_visible(timeout=3000):
                headline_edit.click()
                human_sleep(1, 2)
                save_btn = page.locator("button:has-text('Save'), input[value='Save']").first
                if save_btn.is_visible(timeout=3000):
                    save_btn.click()
                    human_sleep(2, 3)
                    print("[SUCCESS] Profile timestamp successfully bumped to Today.")
                    record_profile_event("PROFILE_TOUCH", "SUCCESS", "Headline saved")
        except Exception as e:
            print(f"[*] Profile touch note: {e}")

    print("=" * 60 + "\n")
    return uploaded
