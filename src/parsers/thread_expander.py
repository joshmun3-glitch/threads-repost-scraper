"""Thread expansion to capture multi-post threads."""

from typing import List, Optional
from playwright.async_api import Page, ElementHandle
from ..utils.logger import get_logger


logger = get_logger(__name__)


class ThreadExpander:
    """Handles expansion of multi-post threads."""

    @staticmethod
    async def is_thread(element: ElementHandle) -> bool:
        """
        Check if a post is part of a multi-post thread.

        Args:
            element: The post element to check

        Returns:
            True if this appears to be a thread with multiple posts
        """
        try:
            # Check for thread indicators in the text
            text = await element.inner_text()

            # Common thread indicators
            thread_indicators = [
                '1/',  # Thread numbering like "1/5"
                '(1/',  # Alternative format
                '🧵',  # Thread emoji
                'Thread:',
                'thread:',
            ]

            for indicator in thread_indicators:
                if indicator in text:
                    logger.debug(f"Found thread indicator: {indicator}")
                    return True

            # Check for truncated text indicators (suggests more content)
            truncation_indicators = [
                '...',  # Ellipsis
            ]

            text_stripped = text.strip()
            for indicator in truncation_indicators:
                if text_stripped.endswith(indicator):
                    logger.debug(f"Found truncation indicator: {indicator}")
                    return True

            # Check if text ends abruptly (with colon, suggesting continuation)
            # But only if the text is reasonably long (> 200 chars)
            if len(text_stripped) > 200 and text_stripped.endswith(':'):
                logger.debug("Text ends with colon and is long - likely truncated thread")
                return True

            # Check if there's a "View post" or "Show thread" type link
            # (Threads often has these for multi-post content)
            links = await element.query_selector_all('a')
            for link in links:
                link_text = await link.inner_text()
                if any(phrase in link_text.lower() for phrase in ['view', 'thread', 'more', 'see more', 'show more']):
                    logger.debug(f"Found 'more' link: {link_text}")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking if thread: {e}")
            return False

    @staticmethod
    async def expand_thread(page: Page, post_url: str, author_username: str) -> List[str]:
        """
        Expand a thread and extract all posts by the original author.

        Args:
            page: Playwright page instance
            post_url: URL of the thread to expand
            author_username: Original author's username

        Returns:
            List of text content from each post in the thread
        """
        thread_posts = []

        try:
            logger.info(f"🔍 Expanding thread: {post_url}")

            # Navigate to the full post page
            full_url = f"https://www.threads.net{post_url}" if post_url.startswith('/') else post_url
            logger.debug(f"Thread URL: {full_url}")

            # Create a new page for thread expansion (to avoid affecting main scraping)
            thread_page = await page.context.new_page()

            try:
                logger.debug(f"Navigating to thread page...")
                await thread_page.goto(full_url, wait_until='load', timeout=30000)
                logger.debug(f"Page loaded, waiting for content...")
                await thread_page.wait_for_timeout(3000)  # Wait for content to load (increased from 2s)

                # Find all post containers on the thread page
                containers = await thread_page.query_selector_all('div[data-pressable-container="true"]')
                logger.info(f"📦 Found {len(containers)} containers in thread page")

                author_post_count = 0
                for i, container in enumerate(containers):
                    # Check if this post is by the original author
                    is_by_author = await ThreadExpander._is_by_author(container, author_username)
                    logger.debug(f"Container {i+1}: by_author={is_by_author}")

                    if is_by_author:
                        author_post_count += 1
                        # Extract text from this post
                        text = await ThreadExpander._extract_thread_post_text(container, author_username)
                        logger.debug(f"Extracted text length: {len(text) if text else 0}")

                        if text and len(text) > 10:  # Only add substantial content
                            thread_posts.append(text)
                            logger.info(f"✅ Added thread post #{len(thread_posts)}: {text[:50]}...")
                        else:
                            logger.debug(f"Skipped container {i+1}: text too short or empty")

                logger.info(f"📊 Found {author_post_count} posts by @{author_username} in thread")

            finally:
                await thread_page.close()

            logger.info(f"✅ Extracted {len(thread_posts)} posts from thread")
            return thread_posts

        except Exception as e:
            logger.warning(f"❌ Error expanding thread: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return thread_posts  # Return what we got so far

    @staticmethod
    async def _is_by_author(container: ElementHandle, author_username: str) -> bool:
        """
        Check if a post container is by the specified author.

        Args:
            container: Post container element
            author_username: Username to check against

        Returns:
            True if post is by the author
        """
        try:
            # Look for username links
            username_links = await container.query_selector_all(f'a[href^="/@{author_username}"]')
            return len(username_links) > 0

        except Exception:
            return False

    @staticmethod
    async def _extract_thread_post_text(container: ElementHandle, author_username: str) -> str:
        """
        Extract text from a single post in a thread.

        Args:
            container: Post container element
            author_username: Author's username to filter out

        Returns:
            Extracted text content
        """
        try:
            full_text = await container.inner_text()
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            filtered_lines = []
            for line in lines:
                # Skip metadata
                if line.lower() == author_username.lower():
                    continue
                if len(line) < 3:
                    continue
                if line.isdigit():
                    continue
                if line.endswith('시간') and len(line) < 10:
                    continue

                filtered_lines.append(line)

            return '\n'.join(filtered_lines)

        except Exception as e:
            logger.warning(f"Error extracting thread post text: {e}")
            return ""

    @staticmethod
    def format_thread_content(thread_posts: List[str]) -> str:
        """
        Format multiple thread posts into a single content block.

        Args:
            thread_posts: List of text from each post in thread

        Returns:
            Formatted thread content
        """
        if not thread_posts:
            return ""

        if len(thread_posts) == 1:
            return thread_posts[0]

        # Format as numbered thread
        formatted = []
        for i, post in enumerate(thread_posts, 1):
            formatted.append(f"[{i}/{len(thread_posts)}]\n{post}")

        return '\n\n---\n\n'.join(formatted)
