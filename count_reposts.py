"""Quick script to count how many reposts are actually on the page."""

import asyncio
from playwright.async_api import async_playwright
import sys

async def count_reposts(username: str):
    """Count total reposts by scrolling to the bottom."""

    print(f"\n{'='*60}")
    print(f"REPOST COUNTER: @{username}")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = f"https://www.threads.net/@{username}/reposts"
        print(f"Loading: {url}\n")

        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)

        # Check login
        if '/login' in page.url:
            print("❌ Need to login first!")
            await browser.close()
            return

        print("Starting scroll test...\n")

        scroll_count = 0
        no_change_count = 0
        previous_count = 0

        while no_change_count < 5:  # Try 5 times with no change
            # Count current posts
            articles = await page.query_selector_all('article')
            current_count = len(articles)

            print(f"Scroll #{scroll_count + 1}: Found {current_count} posts", end='')

            if current_count == previous_count:
                no_change_count += 1
                print(f" (no change, {no_change_count}/5)")
            else:
                no_change_count = 0
                new_posts = current_count - previous_count
                print(f" (+{new_posts} new)")
                previous_count = current_count

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)  # Wait 3 seconds

            scroll_count += 1

            # Safety limit
            if scroll_count > 50:
                print("\n⚠️  Reached 50 scroll limit")
                break

        # Final count
        final_articles = await page.query_selector_all('article')
        final_count = len(final_articles)

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"{'='*60}")
        print(f"Total scrolls: {scroll_count}")
        print(f"Total reposts found: {final_count}")
        print(f"\nYour scraper found: 24")
        print(f"Missing: {final_count - 24}")
        print(f"{'='*60}\n")

        if final_count > 24:
            print("⚠️  ISSUE DETECTED: Many reposts are missing!")
            print("\nPossible solutions:")
            print("1. Increase --wait-time (default is 2, try 5 or 10)")
            print("2. Increase --max-retries (default is 3, try 10 or 20)")
            print("3. Check if selectors need updating")
        else:
            print("✓ Scraper seems to be finding all available posts")

        print("\nBrowser will stay open. Check if reposts look correct.")
        print("Press ENTER to close...")
        input()

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_reposts.py <username>")
        sys.exit(1)

    username = sys.argv[1].lstrip('@')
    asyncio.run(count_reposts(username))
