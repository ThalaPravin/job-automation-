import asyncio
import random
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from playwright.async_api import Page, Locator
from rich.console import Console

from src.config_loader import AppConfig, UserProfile
from src.db import Database
from src.ai_pitcher import PitchGenerator

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class WellfoundApplier:
    def __init__(self, page: Page, config: AppConfig, profile: UserProfile, db: Database):
        self.page = page
        self.config = config
        self.profile = profile
        self.db = db
        self.pitcher = PitchGenerator(profile, use_ai=profile.pitch.use_ai)
        self.screenshots_dir = PROJECT_ROOT / "data" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    def is_blacklisted(self, company_name: str, job_title: str) -> bool:
        for blacklisted_co in self.config.blacklist.companies:
            if blacklisted_co.lower() in company_name.lower():
                return True

        for keyword in self.config.blacklist.title_keywords_exclude:
            if keyword.lower() in job_title.lower():
                return True

        return False

    async def run(self, max_applications: Optional[int] = None):
        limit = max_applications or self.config.safety.max_applications_per_run
        applied_count = 0

        target_url = self.config.search.custom_search_url or "https://wellfound.com/jobs"
        console.print(f"[cyan]Navigating to jobs feed: {target_url}[/cyan]")
        try:
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=40000)
        except Exception as e:
            console.print(f"[yellow]Navigation notice: {e}. Continuing with loaded content...[/yellow]")
        await asyncio.sleep(5)

        # Scroll down progressively to load more listings
        for _ in range(10):
            await self.page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1.5)

        console.print("[cyan]Scanning for open roles...[/cyan]")
        
        job_buttons = await self.page.query_selector_all("button:has-text('Learn more')")
        console.print(f"[green]Found {len(job_buttons)} candidate job listings on current page.[/green]")

        if not job_buttons:
            console.print("[yellow]No 'Learn more' buttons found. Saving debug screenshot to data/feed_debug.png...[/yellow]")
            debug_shot = self.screenshots_dir / "feed_debug.png"
            await self.page.screenshot(path=str(debug_shot))
            return

        for idx, btn in enumerate(job_buttons):
            if applied_count >= limit:
                console.print(f"[bold green]Reached session limit of {limit} applications. Stopping.[/bold green]")
                break

            try:
                # 1. Extract card info directly from the DOM before clicking
                card_info = await btn.evaluate("""el => {
                    let row = el;
                    while (row && !row.className.includes('styles_jobListing') && !row.className.includes('styles_result') && row.tagName !== 'BODY') {
                        row = row.parentElement;
                    }
                    let compEl = null;
                    let curr = el;
                    while (curr && curr.tagName !== 'BODY') {
                        let c = curr.querySelector('a[href*="/company/"]');
                        if (c && c.href && c.href.includes('/company/')) {
                            compEl = c;
                            break;
                        }
                        curr = curr.parentElement;
                    }
                    let companyHref = compEl ? compEl.href : '';
                    let title = '';
                    if (row) {
                        let h = row.querySelector('h2, a[href*="/jobs/"], [data-test*="JobTitle"]');
                        if (h) title = h.innerText.trim();
                        else {
                            let lines = row.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
                            title = lines[0] || '';
                        }
                    }
                    return { companyHref, title };
                }""")

                company_name = "Startup"
                if "/company/" in card_info.get("companyHref", ""):
                    company_name = card_info["companyHref"].split("/company/")[1].split("/")[0].replace("-", " ").title().strip()

                raw_title = card_info.get("title", "")
                title_lines = [l.strip() for l in raw_title.split("\n") if l.strip() and "search" not in l.lower()]
                job_title = title_lines[0] if title_lines else "Backend Engineer"

                job_key = f"{company_name}_{job_title}".replace(" ", "_")

                # Check blacklist
                if self.is_blacklisted(company_name, job_title):
                    console.print(f"[dim]Skipping blacklisted: {company_name} - {job_title}[/dim]")
                    continue

                # Check DB deduplication
                if self.db.is_already_applied(job_key):
                    console.print(f"[dim]Already applied to: {company_name} - {job_title}[/dim]")
                    continue

                console.print(f"\n[bold blue]Processing [{applied_count + 1}/{limit}]: {company_name} - {job_title}[/bold blue]")

                # Scroll into view and click
                await btn.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await btn.click(force=True)
                await asyncio.sleep(4)

                # Find pitch textarea anywhere on page
                textarea = await self.page.query_selector("textarea")
                if not textarea:
                    console.print("[yellow]No pitch textarea on this role (might be external or already applied). Closing.[/yellow]")
                    await self._close_modal()
                    continue

                # Generate master pitch note
                pitch_note = self.pitcher.generate(company_name=company_name, role_title=job_title)
                console.print(f"[dim]Pasting Master Pitch Note ({len(pitch_note)} chars) for {company_name}...[/dim]")
                await textarea.fill(pitch_note)
                await asyncio.sleep(1)

                if self.config.safety.dry_run:
                    console.print(f"[bold yellow][DRY RUN][/bold yellow] Application prepared for {company_name} - {job_title}. Not submitting.")
                    screenshot_file = self.screenshots_dir / f"{abs(hash(job_key))}.png"
                    await self.page.screenshot(path=str(screenshot_file))
                    
                    await self._close_modal()
                    self.db.record_application(
                        job_key=job_key,
                        company_name=company_name,
                        job_title=job_title,
                        job_url=self.page.url,
                        status="DRY_RUN",
                        pitch_note=pitch_note
                    )
                else:
                    # LIVE APPLY SUBMISSION
                    apply_btn = await self.page.query_selector("button:has-text('Apply').w-full, button:has-text('Apply')")
                    if apply_btn and await apply_btn.is_enabled():
                        await apply_btn.click(force=True)
                        await asyncio.sleep(4)
                        console.print(f"[bold green][OK] Successfully applied to {company_name} - {job_title}![/bold green]")
                        self.db.record_application(
                            job_key=job_key,
                            company_name=company_name,
                            job_title=job_title,
                            job_url=self.page.url,
                            status="APPLIED",
                            pitch_note=pitch_note
                        )
                    else:
                        console.print("[red]Could not find or click active Apply button. Closing.[/red]")
                        self.db.record_application(
                            job_key=job_key,
                            company_name=company_name,
                            job_title=job_title,
                            job_url=self.page.url,
                            status="FAILED",
                            pitch_note=pitch_note
                        )
                    await self._close_modal()

                applied_count += 1

                # Randomized human delay between applications
                delay = random.uniform(self.config.safety.min_delay_seconds, self.config.safety.max_delay_seconds)
                console.print(f"[dim]Waiting {delay:.1f}s before next application...[/dim]")
                await asyncio.sleep(delay)

            except Exception as e:
                console.print(f"[red]Error while processing role: {e}[/red]")
                try:
                    await self._close_modal()
                except Exception:
                    pass
                continue

        console.print(f"\n[bold green]Finished run. Successfully processed {applied_count} application(s).[/bold green]")

    async def _close_modal(self):
        try:
            close_btn = await self.page.query_selector(
                "button[class*='closeButton'], button[aria-label*='close' i], button:has-text('✕'), button:has-text('×'), button:has-text('Done'), button:has-text('Dismiss')"
            )
            if close_btn:
                await close_btn.click(force=True)
                await asyncio.sleep(1.5)
            else:
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(1.5)
        except Exception:
            try:
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(1)
            except Exception:
                pass
