"""Debug script to diagnose scraping issues."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import sys

async def debug_reposts(username: str):
    """Debug what elements are found on the reposts page."""

    print(f"\n{'='*60}")
    print(f"DEBUG MODE: Analyzing @{username} reposts page")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        # Launch browser in headed mode
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to reposts page
        url = f"https://www.threads.net/@{username}/reposts"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until='networkidle')

        # Wait a bit for content to load
        await page.wait_for_timeout(5000)

        print("\n--- Page Analysis ---\n")

        # Check if login required
        if '/login' in page.url:
            print("⚠️  Redirected to login page!")
            print("You need to be logged in to view reposts.")
            await browser.close()
            return

        # Try to find article elements
        selectors_to_try = [
            'article',
            'article[role="presentation"]',
            'div[role="article"]',
            'div[data-pressable-container="true"]'
        ]

        for selector in selectors_to_try:
            elements = await page.query_selector_all(selector)
            print(f"Selector '{selector}': Found {len(elements)} elements")

        # Get all articles
        articles = await page.query_selector_all('article')
        print(f"\n✓ Total articles found: {len(articles)}")

        if len(articles) == 0:
            print("\n❌ No articles found! This might be why posts are missing.")
            print("\nTaking screenshot for analysis...")
            await page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved: debug_screenshot.png")
            await browser.close()
            return

        # Analyze first few posts
        print(f"\n--- Analyzing first 5 posts ---\n")

        for i, article in enumerate(articles[:5], 1):
            print(f"\n📍 Post {i}:")

            # Get all text
            full_text = await article.inner_text()
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]

            print(f"  Total lines: {len(lines)}")
            print(f"  First 10 lines:")
            for line in lines[:10]:
                print(f"    {line}")

            # Try to find timestamp
            time_elements = await article.query_selector_all('time')
            if time_elements:
                for time_el in time_elements:
                    datetime_attr = await time_el.get_attribute('datetime')
                    text = await time_el.inner_text()
                    print(f"  ⏰ Time element: datetime='{datetime_attr}', text='{text}'")
            else:
                print(f"  ⚠️  No time elements found")

            # Try to find links
            links = await article.query_selector_all('a[href*="/post/"]')
            if links:
                for link in links[:2]:
                    href = await link.get_attribute('href')
                    print(f"  🔗 Post link: {href}")
            else:
                print(f"  ⚠️  No post links found")

        # Check scroll position and page height
        scroll_info = await page.evaluate("""
            () => ({
                scrollHeight: document.body.scrollHeight,
                clientHeight: document.documentElement.clientHeight,
                scrollY: window.scrollY
            })
        """)

        print(f"\n--- Page Scroll Info ---")
        print(f"  Scroll Height: {scroll_info['scrollHeight']}px")
        print(f"  Client Height: {scroll_info['clientHeight']}px")
        print(f"  Current Scroll: {scroll_info['scrollY']}px")

        # Try scrolling a bit
        print(f"\n--- Testing Scroll ---")
        print("Scrolling down...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        # Check again
        new_articles = await page.query_selector_all('article')
        print(f"Articles after scroll: {len(new_articles)} (was {len(articles)})")

        if len(new_articles) > len(articles):
            print(f"✓ Scroll loaded {len(new_articles) - len(articles)} more posts")
        else:
            print(f"⚠️  No new posts loaded after scroll")

        # Take screenshot
        print(f"\nTaking screenshot...")
        await page.screenshot(path="debug_screenshot.png", full_page=True)
        print("Screenshot saved: debug_screenshot.png")

        # Keep browser open for manual inspection
        print(f"\n{'='*60}")
        print("Browser will stay open for manual inspection.")
        print("Check the Threads page to see if recent posts are visible.")
        print("Press ENTER to close...")
        print(f"{'='*60}\n")

        input()

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_scraper.py <username>")
        sys.exit(1)

    username = sys.argv[1].lstrip('@')
    asyncio.run(debug_reposts(username))
