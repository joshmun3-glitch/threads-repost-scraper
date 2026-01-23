"""Infinite scroll handler for Threads."""

import asyncio
from typing import Optional
from playwright.async_api import Page

from ..utils.logger import get_logger


logger = get_logger(__name__)


class ScrollHandler:
    """Handles infinite scrolling to load all content."""

    @staticmethod
    async def scroll_to_load_all(
        page: Page,
        wait_time: int = 2,
        max_retries: int = 3,
        max_scrolls: Optional[int] = None
    ) -> int:
        """
        Scroll through the page to load all content via infinite scroll.

        Args:
            page: Playwright page instance
            wait_time: Seconds to wait between scrolls
            max_retries: Number of consecutive unchanged heights before stopping
            max_scrolls: Maximum number of scrolls (optional limit)

        Returns:
            Total number of scrolls performed
        """
        logger.info(f"Starting infinite scroll (wait_time={wait_time}s, max_retries={max_retries})")

        previous_height = 0
        previous_post_count = 0
        no_change_count = 0
        scroll_count = 0

        while no_change_count < max_retries:
            # Check if we've hit the scroll limit
            if max_scrolls and scroll_count >= max_scrolls:
                logger.info(f"Reached maximum scroll limit: {max_scrolls}")
                break

            # Get current metrics BEFORE scrolling
            current_height = await page.evaluate("document.body.scrollHeight")
            current_post_count = await page.evaluate("""
                () => document.querySelectorAll('div[data-pressable-container="true"]').length
            """)

            # Scroll to bottom using multiple methods to trigger lazy loading
            await page.evaluate("""
                // Method 1: Smooth scroll to bottom
                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            """)
            await asyncio.sleep(0.5)

            # Method 2: Instant scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

            # Method 3: Scroll by large amount
            await page.evaluate("window.scrollBy(0, 5000)")

            scroll_count += 1

            logger.info(f"Scroll #{scroll_count}: height={current_height}, posts={current_post_count}")

            # Wait for content to load
            await asyncio.sleep(wait_time)

            # Get new metrics AFTER scrolling
            new_height = await page.evaluate("document.body.scrollHeight")
            new_post_count = await page.evaluate("""
                () => document.querySelectorAll('div[data-pressable-container="true"]').length
            """)

            logger.info(f"After scroll: height={new_height}, posts={new_post_count}")

            # Check if EITHER height or post count changed
            height_changed = new_height > current_height
            posts_increased = new_post_count > current_post_count

            if height_changed or posts_increased:
                # New content loaded
                no_change_count = 0
                previous_height = new_height
                previous_post_count = new_post_count
                if posts_increased:
                    logger.info(f"✅ Loaded {new_post_count - current_post_count} new posts")
            else:
                # No new content
                no_change_count += 1
                logger.warning(f"⚠️  No new content ({no_change_count}/{max_retries})")

        logger.info(f"Scrolling complete: {scroll_count} scrolls performed, {previous_post_count} total posts visible")
        return scroll_count

    @staticmethod
    async def scroll_to_element(page: Page, selector: str, timeout: int = 5000) -> bool:
        """
        Scroll to make a specific element visible.

        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            timeout: Timeout in milliseconds

        Returns:
            True if element was found and scrolled to, False otherwise
        """
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                await element.scroll_into_view_if_needed()
                logger.debug(f"Scrolled to element: {selector}")
                return True
        except Exception as e:
            logger.warning(f"Could not scroll to element {selector}: {e}")

        return False

    @staticmethod
    async def wait_for_scroll_end(page: Page, stable_time: float = 1.0) -> None:
        """
        Wait until scrolling has stopped (height remains stable).

        Args:
            page: Playwright page instance
            stable_time: Time in seconds that height must remain stable
        """
        logger.debug("Waiting for scroll to end")

        last_height = await page.evaluate("document.body.scrollHeight")
        stable_duration = 0
        check_interval = 0.1  # Check every 100ms

        while stable_duration < stable_time:
            await asyncio.sleep(check_interval)
            current_height = await page.evaluate("document.body.scrollHeight")

            if current_height == last_height:
                stable_duration += check_interval
            else:
                stable_duration = 0
                last_height = current_height

        logger.debug("Scroll has ended")

    @staticmethod
    async def get_scroll_position(page: Page) -> dict:
        """
        Get current scroll position.

        Args:
            page: Playwright page instance

        Returns:
            Dictionary with scrollY, scrollX, and scrollHeight
        """
        return await page.evaluate("""
            () => ({
                scrollY: window.scrollY,
                scrollX: window.scrollX,
                scrollHeight: document.body.scrollHeight,
                clientHeight: document.documentElement.clientHeight
            })
        """)

    @staticmethod
    async def scroll_by(page: Page, x: int = 0, y: int = 500) -> None:
        """
        Scroll by a specific amount.

        Args:
            page: Playwright page instance
            x: Horizontal scroll amount
            y: Vertical scroll amount
        """
        await page.evaluate(f"window.scrollBy({x}, {y})")
        await asyncio.sleep(0.5)  # Brief pause for rendering
