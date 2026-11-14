"""
Instahyre Session Setup (Multi-Profile):
Run this script to log into your Instahyre account(s).
Usage:
  python setup_session.py --profile sde   (Default: SDE Account)
  python setup_session.py --profile qa    (QA / SDET Account)
"""

import sys
import os
import argparse
import yaml
from playwright.sync_api import sync_playwright
from browser_manager import get_persistent_context, human_sleep

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def load_config():
    config_path = os.path.join(BASE_DIR, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_setup(profile_key: str = "sde"):
    config = load_config()
    profile_cfg = config.get("profiles", {}).get(profile_key, {})
    user_data_dir = profile_cfg.get("user_data_dir", f"browser_profile_{profile_key}")
    profile_title = profile_cfg.get("name", profile_key.upper())

    print("\n" + "=" * 65)
    print(f" INSTAHYRE 1-TIME LOGIN SETUP: [{profile_title.upper()}]")
    print("=" * 65)
    print(f"Browser Session Directory: {user_data_dir}")
    print("-" * 65)
    print("INSTRUCTIONS:")
    print(f" 1. A browser window will open for your '{profile_key.upper()}' Instahyre account.")
    print(" 2. Complete your login manually (using Email/Password, OTP, or Google).")
    print(" 3. Verify that you can see your Instahyre candidate dashboard/opportunities.")
    print(" 4. Return to this terminal and press [ENTER] to confirm and save.")
    print("=" * 65 + "\n")

    with sync_playwright() as p:
        context = get_persistent_context(p, headless=False, user_data_dir=user_data_dir)
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://www.instahyre.com/login/", wait_until="domcontentloaded")
        
        try:
            input(f"Press [ENTER] in this terminal AFTER logging into your {profile_key.upper()} account... ")
        except EOFError:
            pass
            
        print("\nVerifying session...")
        try:
            if "opportunities" not in page.url and "profile" not in page.url:
                page.goto("https://www.instahyre.com/candidate/opportunities/", wait_until="domcontentloaded", timeout=15000)
            else:
                page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass

        human_sleep(2, 3)
        
        current_url = page.url
        cookies = context.cookies()
        insta_cookies = [c for c in cookies if "instahyre" in c.get("domain", "")]
        
        if "login" not in current_url.lower() and len(insta_cookies) > 0:
            print(f"\n[OK] SUCCESS! Authenticated session confirmed ({len(insta_cookies)} cookies saved in {user_data_dir}).")
            print(f"Daily automation for {profile_key.upper()} will now run seamlessly without prompting for passwords.")
        else:
            print(f"\n[*] Current URL: {current_url}")
            print(f"[*] Found {len(insta_cookies)} Instahyre session cookies.")
            if "login" in current_url.lower():
                print("[!] Browser is still on the login page. Please ensure you complete login before pressing ENTER.")

        # Properly close context to flush cookies to SQLite database
        context.close()
        print(f"\nBrowser closed. Setup for [{profile_key.upper()}] complete!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instahyre 1-Time Session Login Setup")
    parser.add_argument("--profile", choices=["sde", "qa"], default="sde", help="Target profile: 'sde' or 'qa'")
    args = parser.parse_args()
    run_setup(args.profile)
