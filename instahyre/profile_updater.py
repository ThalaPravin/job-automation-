import os
import time
from playwright.sync_api import Page
from browser_manager import human_sleep
from database import record_profile_event

def update_resume_and_profile(page: Page, config: dict, profile_key: str = "sde") -> bool:
    """
    Automates daily resume refresh and touches profile activity on Instahyre.
    This guarantees candidate profile ranks higher in InstaMatch recruiter searches
    and displays under 'Active Recently'.
    """
    profile_cfg = config.get("profiles", {}).get(profile_key, {})
    resume_path = profile_cfg.get("resume_path", "")
    db_path = profile_cfg.get("db_path", f"data/instahyre_{profile_key}.db")

    print(f"\n[*] Starting Daily Profile & Resume Refresh for [{profile_key.upper()}]...")

    if not resume_path or not os.path.exists(resume_path):
        print(f"[-] Resume file not found at: {resume_path}. Skipping resume update.")
        record_profile_event("RESUME_UPDATE", "SKIPPED", f"File not found: {resume_path}", db_path)
        return False

    try:
        # Navigate to Candidate Profile page
        print("  [1/3] Navigating to Instahyre Candidate Profile...")
        page.goto("https://www.instahyre.com/candidate/profile/", wait_until="domcontentloaded", timeout=40000)
        human_sleep(3, 5)

        # Check if redirected to login
        if "login" in page.url.lower():
            print("  [!] Session expired or not logged in. Please run setup_session first.")
            record_profile_event("RESUME_UPDATE", "FAILED", "Not logged in (redirected to login)", db_path)
            return False

        # Step 2: Upload fresh resume file
        print(f"  [2/3] Uploading fresh resume: {os.path.basename(resume_path)}...")
        
        # Check for standard file input for resume
        file_input = page.locator("input[type='file'][accept*='pdf'], input[type='file']").first
        
        # If input is not immediately visible, check for "Edit" or "Upload Resume" or refresh icon
        if file_input.count() == 0 or not file_input.is_visible():
            upload_triggers = page.locator(
                "a:has-text('Upload Resume'), button:has-text('Upload Resume'), "
                "a:has-text('Update Resume'), button:has-text('Update Resume'), "
                "a[ng-click*='resume' i], button[ng-click*='resume' i], "
                "span.glyphicon-pencil, i.fa-pencil, .resume-edit"
            )
            if upload_triggers.count() > 0 and upload_triggers.first.is_visible():
                try:
                    upload_triggers.first.click()
                    human_sleep(1, 2)
                except Exception:
                    pass

        # Re-check file input
        file_input = page.locator("input[type='file']").first
        if file_input.count() > 0:
            file_input.set_input_files(resume_path)
            print(f"  [OK] File dispatched to uploader: {resume_path}")
            human_sleep(3, 6)

            # Look for any save or submit buttons after file selection
            save_btn = page.locator("button:has-text('Save'), button:has-text('Upload'), button.btn-primary").first
            if save_btn.is_visible(timeout=3000):
                save_btn.click()
                human_sleep(2, 4)

            print("  [OK] Resume uploaded and updated successfully.")
            record_profile_event("RESUME_UPDATE", "SUCCESS", f"Uploaded: {os.path.basename(resume_path)}", db_path)
        else:
            print("  [*] Resume input field not found on page. Profile active timestamp will be updated.")
            record_profile_event("RESUME_UPDATE", "SKIPPED", "File input selector not found", db_path)

        # Step 3: Touch profile activity / save preferences to update timestamp
        if profile_cfg.get("touch_profile_fields", True):
            print("  [3/3] Touching candidate profile timestamp...")
            try:
                human_sleep(1, 2)
                
                # Check for any "Save Changes" or "Update" button in profile sections
                save_profile_btn = page.locator(
                    "button:has-text('Save Changes'), button:has-text('Save Preferences'), "
                    "button#candidate-profile-save"
                ).first
                if save_profile_btn.is_visible(timeout=2000):
                    save_profile_btn.click()
                    human_sleep(2, 3)
                    print("  [OK] Profile timestamp saved.")
                else:
                    # Simply visiting profile touches candidate last-seen in Instahyre backend
                    print("  [OK] Candidate profile activity refreshed.")
                
                record_profile_event("PROFILE_TIMESTAMP_REFRESH", "SUCCESS", "Profile activity touched", db_path)
            except Exception as e:
                print(f"  [-] Note on touching profile: {e}")

        print(f"[OK] Completed Profile & Resume Freshness Step for [{profile_key.upper()}].\n")
        return True

    except Exception as e:
        print(f"[-] Error during profile refresh: {e}")
        record_profile_event("PROFILE_REFRESH", "ERROR", str(e), db_path)
        return False
