"""
Setup Session (Multi-Profile):
Run this script to log into your Naukri account(s).
Usage:
  python setup_session.py --profile sde   (Default: SDE Account)
  python setup_session.py --profile qa    (QA / SDET Account)
"""

import sys
import argparse
import yaml
from playwright.sync_api import sync_playwright
from browser_manager import get_persistent_context, human_sleep

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_setup(profile_key: str = "sde"):
    config = load_config()
    profile_cfg = config.get("profiles", {}).get(profile_key, config.get("profile", {}))
    user_data_dir = profile_cfg.get("user_data_dir", f"browser_profile_{profile_key}")
    profile_title = profile_cfg.get("name", profile_key.upper())

    print("\n" + "=" * 65)
    print(f" NAUKRI LOGIN SETUP: [{profile_title.upper()}]")
    print("=" * 65)
    print(f"Browser Session Directory: {user_data_dir}")
    print("-" * 65)
    print("INSTRUCTIONS:")
    print(f" 1. A browser window will open for your '{profile_key.upper()}' Naukri account.")
    print(" 2. Complete your login manually (using Email/Password, OTP, or Google).")
    print(" 3. Verify that you can see your Naukri profile / dashboard.")
    print(" 4. Return to this terminal and press [ENTER] to confirm and save.")
    print("=" * 65 + "\n")

    with sync_playwright() as p:
        context = get_persistent_context(p, headless=False, user_data_dir=user_data_dir)
        page = context.pages[0] if context.pages else context.new_page()
        
        page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded")
        
        try:
            input(f"Press [ENTER] in this terminal AFTER logging into your {profile_key.upper()} account... ")
        except EOFError:
            pass
            
        print("\nVerifying session...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        human_sleep(2, 4)
        
        current_url = page.url
        if "profile" in current_url or "homepage" in current_url:
            print(f"\n[✓] SUCCESS! Your authenticated session for [{profile_key.upper()}] is saved in: {user_data_dir}")
            print(f"Daily automation for {profile_key.upper()} will now run without prompting for passwords.")
        else:
            print(f"\n[*] Current URL: {current_url}")
            print("Please ensure you are fully logged in before running daily automation.")

        context.close()
        print(f"\nBrowser closed. Setup for [{profile_key.upper()}] complete!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naukri 1-Time Session Login Setup")
    parser.add_argument("--profile", choices=["sde", "qa"], default="sde", help="Target profile: 'sde' or 'qa'")
    args = parser.parse_args()
    run_setup(args.profile)
