"""Inspect the actual content inside the div containers."""

import asyncio
from playwright.async_api import async_playwright
import sys

async def inspect_posts(username: str):
    """Inspect what's inside the post containers."""

    print(f"\n{'='*60}")
    print(f"INSPECTING POST STRUCTURE: @{username}")
    print(f"{'='*60}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = f"https://www.threads.net/@{username}/reposts"
        print(f"Loading: {url}\n")
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(5000)

        if '/login' in page.url:
            print("❌ Need to login first!")
            await browser.close()
            return

        # Find the containers
        containers = await page.query_selector_all('div[data-pressable-container="true"]')
        print(f"✓ Found {len(containers)} div[data-pressable-container='true'] elements\n")

        if len(containers) == 0:
            print("❌ No containers found!")
            await browser.close()
            return

        # Inspect first 3 containers
        for i, container in enumerate(containers[:3], 1):
            print(f"\n{'='*60}")
            print(f"CONTAINER #{i}")
            print(f"{'='*60}\n")

            # Get all text
            full_text = await container.inner_text()
            print(f"--- Full Text Content ---")
            print(full_text[:500])  # First 500 chars
            print("\n")

            # Try to find time elements
            print(f"--- Time Elements ---")
            time_elements = await container.query_selector_all('time')
            if time_elements:
                for t in time_elements:
                    dt = await t.get_attribute('datetime')
                    text = await t.inner_text()
                    print(f"  <time datetime='{dt}'>{text}</time>")
            else:
                print("  No <time> elements found")

            # Try to find links
            print(f"\n--- Links (href) ---")
            links = await container.query_selector_all('a[href]')
            for link in links[:5]:  # First 5 links
                href = await link.get_attribute('href')
                text = await link.inner_text()
                print(f"  <a href='{href}'>{text[:30]}</a>")

            # Try to find post links specifically
            print(f"\n--- Post Links (containing /post/) ---")
            post_links = await container.query_selector_all('a[href*="/post/"]')
            if post_links:
                for link in post_links:
                    href = await link.get_attribute('href')
                    print(f"  {href}")
            else:
                print("  No /post/ links found")

            # Try different text selectors
            print(f"\n--- Text Content by Selector ---")
            selectors_to_try = [
                'div[dir="auto"]',
                'span[dir="auto"]',
                'div',
                'span'
            ]

            for selector in selectors_to_try:
                elements = await container.query_selector_all(selector)
                if elements:
                    # Get first few text samples
                    samples = []
                    for el in elements[:3]:
                        text = await el.inner_text()
                        if text and text.strip() and len(text.strip()) > 5:
                            samples.append(text.strip()[:50])

                    if samples:
                        print(f"\n  '{selector}' found {len(elements)} elements:")
                        for s in samples[:3]:
                            print(f"    - {s}")

            # Get HTML structure
            print(f"\n--- HTML Structure (first 800 chars) ---")
            html = await container.inner_html()
            print(html[:800])

        print(f"\n\n{'='*60}")
        print("Analysis complete. Browser will stay open.")
        print("Scroll down and check if more posts load.")
        print("Press ENTER to close...")
        print(f"{'='*60}\n")

        input()
        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_posts.py <username>")
        sys.exit(1)

    username = sys.argv[1].lstrip('@')
    asyncio.run(inspect_posts(username))
