import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page
from rich.console import Console

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

STEALTH_JS = """
// Overwrite the 'navigator.webdriver' property to prevent detection
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Mock plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Mock languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Mock window.chrome
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};
"""

class BrowserManager:
    def __init__(self, browser_config, headless: bool = False):
        self.config = browser_config
        self.headless = headless
        self.playwright = None
        self.context: BrowserContext = None
        self.profile_dir = PROJECT_ROOT / self.config.user_data_dir

    async def start(self) -> Page:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = await async_playwright().start()

        if self.config.use_cdp:
            console.print(f"[cyan]Connecting to existing Chrome instance via CDP at {self.config.cdp_url}...[/cyan]")
            browser = await self.playwright.chromium.connect_over_cdp(self.config.cdp_url)
            self.context = browser.contexts[0] if browser.contexts else await browser.new_context()
        else:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--start-maximized",
            ]
            
            console.print(f"[cyan]Launching browser with profile: {self.profile_dir}[/cyan]")
            launch_kwargs = {
                "user_data_dir": str(self.profile_dir),
                "headless": self.headless,
                "args": args,
                "viewport": None,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                "slow_mo": 50,
            }
            chrome_path = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            if chrome_path.exists():
                launch_kwargs["channel"] = "chrome"

            self.context = await self.playwright.chromium.launch_persistent_context(**launch_kwargs)

        # Add stealth init script
        await self.context.add_init_script(STEALTH_JS)
        
        page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        page.set_default_timeout(45000)
        return page

    async def close(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
