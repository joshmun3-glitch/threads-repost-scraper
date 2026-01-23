"""Debug script to capture what the browser actually sees."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def debug_page_state(username: str):
    """
    Open the page, take screenshots, and dump HTML to see what's happening.
    """
    print("\n" + "="*60)
    print("DEBUG PAGE STATE")
    print("="*60)

    # Load session if it exists
    session_file = Path("session.json")

    async with async_playwright() as p:
        # Launch in headed mode
        browser = await p.chromium.launch(headless=False)

        # Load session
        context_options = {}
        if session_file.exists():
            print(f"Loading session from {session_file}")
            import json
            with open(session_file, 'r') as f:
                context_options['storage_state'] = json.load(f)

        context = await browser.new_context(**context_options)
        page = await context.new_page()

        # Navigate to reposts page
        url = f"https://www.threads.net/@{username}/reposts"
        print(f"\nNavigating to: {url}")
        await page.goto(url, wait_until='load', timeout=60000)

        # Wait for initial load
        print("Waiting 10 seconds for page to load...")
        await page.wait_for_timeout(10000)

        # Take screenshot
        screenshot_path = f"debug_screenshot_1_initial.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")

        # Get page info
        current_url = page.url
        print(f"\nCurrent URL: {current_url}")

        # Check if logged in
        if '/login' in current_url:
            print("❌ REDIRECTED TO LOGIN - Session is invalid!")
        else:
            print("✅ Not on login page")

        # Count posts
        post_count = await page.evaluate("""
            () => document.querySelectorAll('div[data-pressable-container="true"]').length
        """)
        print(f"Post containers found: {post_count}")

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")

        # Try to scroll
        print("\nAttempting to scroll...")
        for i in range(3):
            print(f"  Scroll #{i+1}")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

            new_count = await page.evaluate("""
                () => document.querySelectorAll('div[data-pressable-container="true"]').length
            """)
            print(f"  Posts after scroll: {new_count}")

            if new_count > post_count:
                print(f"  ✅ Loaded {new_count - post_count} new posts!")
                post_count = new_count
            else:
                print(f"  ⚠️  No new posts loaded")

        # Take screenshot after scrolling
        screenshot_path = f"debug_screenshot_2_after_scroll.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nScreenshot saved: {screenshot_path}")

        # Save HTML
        html = await page.content()
        html_path = "debug_page.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML saved: {html_path}")

        # Get all text on page
        all_text = await page.evaluate("() => document.body.innerText")

        # Check for error messages
        if "something went wrong" in all_text.lower():
            print("\n❌ ERROR MESSAGE DETECTED ON PAGE")
        if "try again" in all_text.lower():
            print("\n❌ 'TRY AGAIN' MESSAGE DETECTED")
        if "not available" in all_text.lower():
            print("\n⚠️  'NOT AVAILABLE' MESSAGE DETECTED")

        print("\n" + "="*60)
        print("Browser will stay open. Check the page manually.")
        print("Close the browser window when done.")
        print("="*60)

        # Keep browser open
        input("\nPress ENTER to close browser...")

        await browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python debug_page_state.py <username>")
        sys.exit(1)

    username = sys.argv[1].lstrip('@')
    asyncio.run(debug_page_state(username))
