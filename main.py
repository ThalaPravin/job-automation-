import argparse
import asyncio
import sys
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config_loader import get_config, get_profile
from src.db import Database
from src.browser import BrowserManager
from src.auth import ensure_authenticated
from src.applier import WellfoundApplier

console = Console()

def show_stats(db: Database):
    stats = db.get_stats()
    console.print("\n[bold cyan]=== Application Statistics ===[/bold cyan]")
    table = Table(title="Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    for status, count in stats.items():
        table.add_row(status.upper(), str(count))
    console.print(table)

    recent = db.get_all_applications(limit=15)
    if recent:
        console.print("\n[bold cyan]Recent Applications:[/bold cyan]")
        rec_table = Table()
        rec_table.add_column("Company", style="cyan")
        rec_table.add_column("Title", style="green")
        rec_table.add_column("Status", style="yellow")
        rec_table.add_column("Applied At", style="dim")
        for item in recent:
            rec_table.add_row(item["company_name"], item["job_title"], item["status"], str(item["applied_at"]))
        console.print(rec_table)

async def run_automation(dry_run: bool, limit: int, login_only: bool = False):
    config = get_config()
    profile = get_profile()
    db = Database()

    # Override dry-run if flag explicitly specified
    if dry_run is not None:
        config.safety.dry_run = dry_run

    console.print(f"[bold cyan]Starting Wellfound Bot... (Mode: {'DRY RUN' if config.safety.dry_run else 'LIVE APPLY'})[/bold cyan]")
    console.print(f"Candidate: [green]{profile.candidate.full_name}[/green] ({profile.candidate.email})")

    browser_mgr = BrowserManager(config.browser, headless=config.safety.headless)
    page = await browser_mgr.start()

    try:
        authenticated = await ensure_authenticated(page)
        if not authenticated:
            console.print("[red]Could not verify authentication. Exiting.[/red]")
            return

        if login_only:
            console.print("[bold green]Login completed and session profile saved! You can now run --dry-run or --apply.[/bold green]")
            return

        applier = WellfoundApplier(page, config, profile, db)
        await applier.run(max_applications=limit)

    finally:
        console.print("[cyan]Closing browser session...[/cyan]")
        await browser_mgr.close()

def main():
    parser = argparse.ArgumentParser(description="Wellfound Job Application Automation Bot")
    parser.add_argument("--login", action="store_true", help="Launch browser to manually log into Wellfound and save cookies/session")
    parser.add_argument("--dry-run", action="store_true", help="Run without submitting applications (generates notes, takes screenshots)")
    parser.add_argument("--apply", action="store_true", help="Live apply to matching jobs")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of applications for this run")
    parser.add_argument("--stats", action="store_true", help="Show application history and statistics")

    args = parser.parse_args()
    db = Database()

    if args.stats:
        show_stats(db)
        return

    # Determine mode
    dry_run = True
    if args.apply:
        dry_run = False
    elif args.dry_run:
        dry_run = True

    asyncio.run(run_automation(dry_run=dry_run, limit=args.limit, login_only=args.login))

if __name__ == "__main__":
    main()
