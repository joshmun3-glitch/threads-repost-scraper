"""Parser for extracting repost data from Threads DOM elements."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from playwright.async_api import ElementHandle, Page
from dateutil import parser as date_parser

from .selectors import SELECTORS
from .thread_expander import ThreadExpander
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
    is_thread: bool = False
    thread_post_count: int = 1

    def __str__(self):
        """String representation."""
        thread_info = f" [{self.thread_post_count} posts]" if self.is_thread else ""
        return f"@{self.author_username}{thread_info}: {self.text[:50]}..."


class PostParser:
    """Parser for extracting data from Threads post elements."""

    @staticmethod
    async def parse_post_element(
        element: ElementHandle,
        page: Optional[Page] = None,
        expand_threads: bool = True
    ) -> Optional[RepostData]:
        """
        Parse a single post element to extract repost data.

        Args:
            element: Playwright ElementHandle for the post
            page: Optional Page instance for thread expansion
            expand_threads: Whether to expand multi-post threads

        Returns:
            RepostData object or None if parsing fails

        Raises:
            ParsingError: If critical data cannot be extracted
        """
        try:
            # Extract author information FIRST
            author_username = await PostParser._extract_author_username(element)
            author_name = await PostParser._extract_author_name(element)

            # Extract text content (now we can filter out author info)
            text = await PostParser._extract_text(element, author_username, author_name)

            # Check if this is a multi-post thread
            is_thread = False
            thread_post_count = 1
            post_url = None

            if expand_threads and page:
                is_thread = await ThreadExpander.is_thread(element)

                if is_thread:
                    logger.info(f"🧵 Detected thread post by @{author_username}")
                    # Get the post URL first
                    post_url = await PostParser._extract_post_url(element)

                    if post_url:
                        logger.info(f"🧵 Expanding thread from URL: {post_url}")
                        # Expand the thread to get all posts
                        thread_posts = await ThreadExpander.expand_thread(page, post_url, author_username)

                        if len(thread_posts) > 1:
                            # Format as a complete thread
                            text = ThreadExpander.format_thread_content(thread_posts)
                            thread_post_count = len(thread_posts)
                            logger.info(f"✅ Expanded thread with {thread_post_count} posts")
                        elif len(thread_posts) == 1:
                            # Use the expanded content (might be cleaner)
                            text = thread_posts[0]
                            logger.info(f"ℹ️  Thread had only 1 post, using expanded content")
                        else:
                            logger.warning(f"⚠️  Thread expansion returned no posts, using original text")
                    else:
                        logger.warning(f"⚠️  Could not extract post URL for thread expansion")

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

            # Extract timestamp
            timestamp, raw_timestamp = await PostParser._extract_timestamp(element)

            # Extract post URL (if not already extracted for thread expansion)
            if not is_thread or not post_url:
                post_url = await PostParser._extract_post_url(element)

            # Create RepostData object
            repost = RepostData(
                text=text or "[No text content]",
                author_username=author_username or "unknown",
                author_name=author_name or "Unknown",
                timestamp=timestamp,
                post_url=post_url or "",
                raw_timestamp=raw_timestamp,
                is_thread=is_thread,
                thread_post_count=thread_post_count
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
                            repost = await PostParser.parse_post_element(element, page=page, expand_threads=True)
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

        # Log date range of scraped posts
        if reposts:
            dates = [r.timestamp for r in reposts if r.timestamp]
            if dates:
                oldest = min(dates)
                newest = max(dates)
                logger.info(f"Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")

        return reposts

    @staticmethod
    async def _extract_text(
        element: ElementHandle,
        author_username: Optional[str] = None,
        author_name: Optional[str] = None
    ) -> str:
        """
        Extract text content from post element.

        Args:
            element: The post element
            author_username: Author username to filter out
            author_name: Author name to filter out

        Returns:
            Extracted text content
        """
        # NEW STRATEGY: For div[data-pressable-container="true"] structure
        # The full post text is best found by getting innerText and filtering out metadata

        try:
            # Get all text from the container
            full_text = await element.inner_text()
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            # Filter out common metadata patterns
            filtered_lines = []
            skip_patterns = [
                author_username,
                author_name,
                'econ threads',  # hashtag
                '번역하기',  # translate button
            ]

            for line in lines:
                # Skip author info
                if author_username and line.lower() == author_username.lower():
                    continue
                if author_name and line.lower() == author_name.lower():
                    continue

                # Skip short single-word lines that are likely UI elements
                if len(line) < 3:
                    continue

                # Skip lines that are just numbers (likes, shares, etc)
                if line.isdigit():
                    continue

                # Skip time-related text like "17시간", "19시간"
                if line.endswith('시간') and len(line) < 10:
                    continue

                # Skip hashtags alone
                if line.startswith('#') and ' ' not in line:
                    continue

                # Keep substantial lines
                filtered_lines.append(line)

            # Join the filtered content
            if filtered_lines:
                # Remove the first line if it's just the username
                if filtered_lines and author_username and filtered_lines[0].lower() == author_username.lower():
                    filtered_lines = filtered_lines[1:]

                content = '\n'.join(filtered_lines)

                # If we got substantial content, return it
                if len(content) > 10:
                    return content

            # Fallback: Try span[dir="auto"] which often has the main text
            span_elements = await element.query_selector_all('span[dir="auto"]')
            for span in span_elements:
                text = await span.inner_text()
                if text and len(text) > 50:  # Likely main content if long enough
                    # Make sure it's not just the username
                    if author_username and text.lower() != author_username.lower():
                        return text.strip()

            # Last resort: return filtered lines even if short
            if filtered_lines:
                return '\n'.join(filtered_lines)

            return full_text.strip() if full_text else ""

        except Exception as e:
            logger.warning(f"Error extracting text: {e}")
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
