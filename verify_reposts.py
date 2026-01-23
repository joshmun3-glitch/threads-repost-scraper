"""Manual verification script to check how many reposts actually exist."""

import asyncio
from playwright.async_api import async_playwright


async def verify_reposts(username: str):
    """
    Open the reposts page in a browser and keep it open for manual verification.

    This helps determine if the scraper is missing posts or if there genuinely
    are only a few reposts available.
    """
    print("\n" + "="*60)
    print("MANUAL REPOST VERIFICATION")
    print("="*60)
    print(f"Opening reposts page for @{username}...")
    print("\nInstructions:")
    print("1. The browser will open to your reposts page")
    print("2. Manually scroll down to load all reposts")
    print("3. Count how many reposts are visible")
    print("4. Close the browser when done")
    print("="*60 + "\n")

    async with async_playwright() as p:
        # Launch browser in headed mode
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to reposts page
        url = f"https://www.threads.net/@{username}/reposts"
        print(f"Navigating to: {url}\n")
        await page.goto(url)

        # Wait for initial load
        await page.wait_for_timeout(5000)

        # Count visible posts
        post_count = await page.evaluate("""
            () => document.querySelectorAll('div[data-pressable-container="true"]').length
        """)

        print(f"Initial post count: {post_count}")
        print("\nNow scroll down manually to load all reposts...")
        print("The browser will stay open until you close it.\n")

        # Keep browser open until user closes it
        try:
            while True:
                await asyncio.sleep(5)
                # Update count
                post_count = await page.evaluate("""
                    () => document.querySelectorAll('div[data-pressable-container="true"]').length
                """)
                print(f"Current post count: {post_count}")
        except Exception:
            pass

        await browser.close()
        print("\nBrowser closed.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python verify_reposts.py <username>")
        sys.exit(1)

    username = sys.argv[1].lstrip('@')
    asyncio.run(verify_reposts(username))
