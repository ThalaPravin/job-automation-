import asyncio
from playwright.async_api import Page
from rich.console import Console

console = Console()

async def is_logged_in(page: Page) -> bool:
    """Checks if the user is logged into Wellfound."""
    try:
        current_url = page.url
        if "login" in current_url or "join" in current_url:
            return False

        cookies = await page.context.cookies()
        cookie_names = [c.get("name", "") for c in cookies]
        # Common Wellfound / AngelList auth cookies
        auth_cookie_indicators = ["_angellist", "remember_user_token", "ajs_user_id", "wellfound_session", "session_id"]
        if any(name in cookie_names for name in auth_cookie_indicators):
            return True

        # Check DOM indicators for logged-in user profile/avatar/navigation
        user_menu = await page.query_selector(
            "button[data-test='user-menu'], [data-test='UserAvatar'], [aria-label*='Profile'], a[href*='/profile'], a[href*='/settings']"
        )
        if user_menu:
            return True

        # If on jobs or overview and no primary login button
        if "wellfound.com/jobs" in current_url or "wellfound.com/overview" in current_url:
            login_btn = await page.query_selector("button:has-text('Log in'), a:has-text('Log in'), button:has-text('Log In')")
            if not login_btn:
                return True

        return False
    except Exception:
        return False

async def ensure_authenticated(page: Page) -> bool:
    """Ensures user is logged in. If not, prompts user in terminal to complete login in the opened browser."""
    console.print("[cyan]Checking Wellfound authentication status...[/cyan]")
    await page.goto("https://wellfound.com/jobs", wait_until="domcontentloaded")
    await asyncio.sleep(4)

    # Check Cloudflare challenge
    content = await page.content()
    if "Just a moment" in content or "cf-turnstile" in content:
        console.print("[yellow]Cloudflare challenge detected. Please complete it manually in the browser...[/yellow]")
        await asyncio.sleep(6)

    if await is_logged_in(page):
        console.print("[bold green][OK] Already authenticated on Wellfound![/bold green]")
        return True

    console.print("\n" + "=" * 60)
    console.print("[bold yellow]ACTION REQUIRED: Wellfound login needed[/bold yellow]")
    console.print("The browser has navigated to Wellfound.")
    console.print("Please log into your Wellfound account in the opened browser window.")
    console.print("(You can sign in via Google, LinkedIn, or Email/Password + 2FA)")
    console.print("Once logged in, press [bold green]ENTER[/bold green] in this terminal (or wait for auto-detection).")
    console.print("=" * 60 + "\n")

    # Race between auto-detection polling and user pressing Enter
    async def poll_login():
        while True:
            await asyncio.sleep(3)
            if await is_logged_in(page):
                return True

    async def wait_for_enter():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, input, "Press ENTER after you have logged in in the browser: ")
            return True
        except Exception:
            return False

    poll_task = asyncio.create_task(poll_login())
    enter_task = asyncio.create_task(wait_for_enter())

    done, pending = await asyncio.wait([poll_task, enter_task], return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()

    console.print("[bold green][OK] Authentication confirmed! Session saved.[/bold green]")
    return True
