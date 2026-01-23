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
        no_change_count = 0
        scroll_count = 0

        while no_change_count < max_retries:
            # Check if we've hit the scroll limit
            if max_scrolls and scroll_count >= max_scrolls:
                logger.info(f"Reached maximum scroll limit: {max_scrolls}")
                break

            # Get current scroll height
            current_height = await page.evaluate("document.body.scrollHeight")

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            scroll_count += 1

            logger.debug(f"Scroll #{scroll_count}: height={current_height}")

            # Wait for content to load
            await asyncio.sleep(wait_time)

            # Get new height
            new_height = await page.evaluate("document.body.scrollHeight")

            # Also count visible post elements to better detect new content
            try:
                post_count = await page.evaluate("""
                    () => document.querySelectorAll('div[data-pressable-container="true"]').length
                """)
                logger.debug(f"Visible posts: {post_count}")
            except Exception:
                pass

            # Check if height changed
            if new_height == current_height:
                no_change_count += 1
                logger.debug(f"No height change ({no_change_count}/{max_retries})")
            else:
                no_change_count = 0
                previous_height = new_height

        logger.info(f"Scrolling complete: {scroll_count} scrolls performed")
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
