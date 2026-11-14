import os
import random
import time
from playwright.sync_api import BrowserContext, Playwright

def get_persistent_context(
    playwright_instance: Playwright,
    headless: bool = False,
    user_data_dir: str = "browser_profile"
) -> BrowserContext:
    """
    Launches a persistent Chromium context with stealth configurations for Instahyre.
    Reuses user_data_dir so active login cookies and session tokens persist.
    """
    os.makedirs(user_data_dir, exist_ok=True)
    
    args = [
        "--disable-blink-features=AutomationControlled",
        "--start-maximized",
        "--no-sandbox",
        "--disable-infobars",
        "--disable-extensions-except",
        "--disable-dev-shm-usage"
    ]
    
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    context = playwright_instance.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        args=args,
        user_agent=user_agent,
        viewport=None,  # Takes maximized window size
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        ignore_default_args=["--enable-automation"]
    )

    # Injected stealth script to mask navigator.webdriver and common bot signals
    stealth_script = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    window.navigator.chrome = {
        runtime: {}
    };
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'hi']
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    """
    context.add_init_script(stealth_script)
    return context

def human_sleep(min_sec: float = 2.0, max_sec: float = 4.0) -> None:
    """Sleeps for a randomized duration to mimic human browsing behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
