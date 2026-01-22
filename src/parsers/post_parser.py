"""Parser for extracting repost data from Threads DOM elements."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from playwright.async_api import ElementHandle, Page
from dateutil import parser as date_parser

from .selectors import SELECTORS
from ..utils.logger import get_logger
from ..utils.exceptions import ParsingError


logger = get_logger(__name__)


@dataclass
class RepostData:
    """Data model for a single repost."""

    text: str
    author_username: str
    author_name: str
    timestamp: Optional[datetime]
    post_url: str
    is_deleted: bool = False
    is_private: bool = False
    raw_timestamp: Optional[str] = None

    def __str__(self):
        """String representation."""
        return f"@{self.author_username}: {self.text[:50]}..."


class PostParser:
    """Parser for extracting data from Threads post elements."""

    @staticmethod
    async def parse_post_element(element: ElementHandle) -> Optional[RepostData]:
        """
        Parse a single post element to extract repost data.

        Args:
            element: Playwright ElementHandle for the post

        Returns:
            RepostData object or None if parsing fails

        Raises:
            ParsingError: If critical data cannot be extracted
        """
        try:
            # Extract text content
            text = await PostParser._extract_text(element)

            # Check if post is deleted or unavailable
            if PostParser._is_deleted(text):
                logger.debug("Skipping deleted/unavailable post")
                return RepostData(
                    text="[Post unavailable]",
                    author_username="unknown",
                    author_name="Unknown",
                    timestamp=None,
                    post_url="",
                    is_deleted=True
                )

            # Extract author information
            author_username = await PostParser._extract_author_username(element)
            author_name = await PostParser._extract_author_name(element)

            # Extract timestamp
            timestamp, raw_timestamp = await PostParser._extract_timestamp(element)

            # Extract post URL
            post_url = await PostParser._extract_post_url(element)

            # Create RepostData object
            repost = RepostData(
                text=text or "[No text content]",
                author_username=author_username or "unknown",
                author_name=author_name or "Unknown",
                timestamp=timestamp,
                post_url=post_url or "",
                raw_timestamp=raw_timestamp
            )

            logger.debug(f"Parsed repost: @{repost.author_username}")
            return repost

        except Exception as e:
            logger.warning(f"Failed to parse post element: {e}")
            raise ParsingError(f"Could not parse post: {e}")

    @staticmethod
    async def parse_page_reposts(page: Page) -> List[RepostData]:
        """
        Parse all repost elements on a page.

        Args:
            page: Playwright Page instance

        Returns:
            List of RepostData objects
        """
        logger.info("Parsing all reposts from page")

        reposts = []
        errors = 0

        # Find all post elements
        for selector in SELECTORS.REPOST_ITEM:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements using selector: {selector}")

                    for i, element in enumerate(elements):
                        try:
                            repost = await PostParser.parse_post_element(element)
                            if repost:
                                reposts.append(repost)
                        except ParsingError as e:
                            logger.warning(f"Error parsing element {i}: {e}")
                            errors += 1

                    # If we found elements, don't try other selectors
                    break

            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        logger.info(f"Parsed {len(reposts)} reposts ({errors} errors)")
        return reposts

    @staticmethod
    async def _extract_text(element: ElementHandle) -> str:
        """Extract text content from post element."""
        for selector in SELECTORS.POST_TEXT:
            try:
                text_element = await element.query_selector(selector)
                if text_element:
                    text = await text_element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue

        # Fallback: get all text from element
        try:
            return (await element.inner_text()).strip()
        except Exception:
            return ""

    @staticmethod
    async def _extract_author_username(element: ElementHandle) -> Optional[str]:
        """Extract author username from post element."""
        for selector in SELECTORS.AUTHOR_USERNAME:
            try:
                username_element = await element.query_selector(selector)
                if username_element:
                    # Try to get from href attribute
                    href = await username_element.get_attribute('href')
                    if href and '/@' in href:
                        username = href.split('/@')[-1].split('/')[0]
                        return username

                    # Fallback: get text content
                    text = await username_element.inner_text()
                    if text:
                        return text.strip().lstrip('@')

            except Exception:
                continue

        return None

    @staticmethod
    async def _extract_author_name(element: ElementHandle) -> Optional[str]:
        """Extract author display name from post element."""
        for selector in SELECTORS.AUTHOR_NAME:
            try:
                name_elements = await element.query_selector_all(selector)
                # Usually the first or second span contains the name
                for name_element in name_elements[:3]:
                    text = await name_element.inner_text()
                    if text and len(text) > 0 and not text.startswith('@'):
                        return text.strip()
            except Exception:
                continue

        return None

    @staticmethod
    async def _extract_timestamp(element: ElementHandle) -> tuple[Optional[datetime], Optional[str]]:
        """Extract and parse timestamp from post element."""
        for selector in SELECTORS.TIMESTAMP:
            try:
                time_element = await element.query_selector(selector)
                if time_element:
                    # Try datetime attribute first
                    datetime_attr = await time_element.get_attribute('datetime')
                    if datetime_attr:
                        try:
                            parsed_time = date_parser.parse(datetime_attr)
                            return parsed_time, datetime_attr
                        except Exception:
                            pass

                    # Fallback: try to parse text content
                    text = await time_element.inner_text()
                    if text:
                        try:
                            parsed_time = date_parser.parse(text)
                            return parsed_time, text
                        except Exception:
                            return None, text

            except Exception:
                continue

        return None, None

    @staticmethod
    async def _extract_post_url(element: ElementHandle) -> Optional[str]:
        """Extract post URL from post element."""
        for selector in SELECTORS.POST_LINK:
            try:
                link_element = await element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        # Make it a full URL if it's relative
                        if href.startswith('/'):
                            href = f"https://www.threads.net{href}"
                        return href
            except Exception:
                continue

        return None

    @staticmethod
    def _is_deleted(text: str) -> bool:
        """Check if post text indicates deleted/unavailable content."""
        if not text:
            return False

        deleted_keywords = [
            'unavailable',
            'deleted',
            'removed',
            'no longer available',
            'not available',
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in deleted_keywords)
