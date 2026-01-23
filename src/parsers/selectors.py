"""CSS and attribute selectors for Threads elements.

Note: Threads uses obfuscated CSS classes that change frequently.
These selectors use attribute-based targeting for better stability.
Selectors may need updates as Threads' HTML structure changes.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ThreadsSelectors:
    """Selectors for Threads page elements."""

    # Post/Repost containers
    # These are the main article elements that contain individual posts
    REPOST_ITEM: List[str] = None
    POST_CONTAINER: List[str] = None

    # Text content
    POST_TEXT: List[str] = None

    # Author information
    AUTHOR_USERNAME: List[str] = None
    AUTHOR_NAME: List[str] = None
    AUTHOR_LINK: List[str] = None

    # Timestamp
    TIMESTAMP: List[str] = None
    TIME_ELEMENT: List[str] = None

    # Post URL/Link
    POST_LINK: List[str] = None

    # Metadata indicators
    REPOST_INDICATOR: List[str] = None
    DELETED_INDICATOR: List[str] = None

    def __post_init__(self):
        """Initialize selector lists with fallbacks."""

        # Post/Repost containers - try multiple selectors
        # Note: Threads structure changes frequently, order matters!
        self.REPOST_ITEM = [
            'div[data-pressable-container="true"]',  # Current working selector (2026-01)
            'article[role="presentation"]',
            'div[role="article"]',
            'article',
        ]

        self.POST_CONTAINER = [
            'div[dir="auto"]',
            'article > div',
        ]

        # Text content - look for text containers
        # Try multiple strategies to find the actual post content
        self.POST_TEXT = [
            # Strategy 1: Direct text containers with dir attribute
            'div[dir="auto"]:not([role="button"])',
            'span[dir="auto"]:not([role="button"])',

            # Strategy 2: Look within the article/post container
            'article div[dir="auto"]',
            'article span',

            # Strategy 3: Text content divs (common patterns)
            'div[style*="text"] span',
            'div[class*="text"] span',

            # Strategy 4: Any div with auto direction (common for text content)
            'div[dir="auto"]',
            'span[dir="auto"]',

            # Strategy 5: Fallback to any span elements
            'span',
            'div',
        ]

        # Author username - typically in links starting with /@
        self.AUTHOR_USERNAME = [
            'a[href^="/@"]',
            'a[role="link"][href*="@"]',
            'span[dir="ltr"]',
        ]

        # Author display name
        self.AUTHOR_NAME = [
            'span[dir="auto"]',
            'div[dir="auto"] span',
        ]

        # Author link
        self.AUTHOR_LINK = [
            'a[href^="/@"]',
            'a[role="link"]',
        ]

        # Timestamp - look for time elements
        self.TIMESTAMP = [
            'time[datetime]',
            'time',
            'a[href*="/post/"] time',
        ]

        self.TIME_ELEMENT = [
            'time',
            'span[role="link"] time',
        ]

        # Post link - links to individual posts
        self.POST_LINK = [
            'a[href*="/post/"]',
            'a[role="link"][href*="/post/"]',
        ]

        # Repost indicator
        self.REPOST_INDICATOR = [
            'svg[aria-label*="repost"]',
            'svg[aria-label*="Repost"]',
            'div[aria-label*="reposted"]',
        ]

        # Deleted/unavailable content
        self.DELETED_INDICATOR = [
            'text=unavailable',
            'text=deleted',
            'text=This post is unavailable',
        ]

    def get_selector_chain(self, selector_list: List[str]) -> str:
        """
        Convert a list of fallback selectors into a comma-separated chain.

        Args:
            selector_list: List of CSS selectors

        Returns:
            Comma-separated selector string
        """
        return ', '.join(selector_list)


# Global instance for easy access
SELECTORS = ThreadsSelectors()


# Helper functions for common selector patterns
def get_post_items_selector() -> str:
    """Get selector for all post items."""
    return SELECTORS.get_selector_chain(SELECTORS.REPOST_ITEM)


def get_post_text_selector() -> str:
    """Get selector for post text content."""
    return SELECTORS.get_selector_chain(SELECTORS.POST_TEXT)


def get_author_username_selector() -> str:
    """Get selector for author username."""
    return SELECTORS.get_selector_chain(SELECTORS.AUTHOR_USERNAME)


def get_timestamp_selector() -> str:
    """Get selector for timestamp."""
    return SELECTORS.get_selector_chain(SELECTORS.TIMESTAMP)


def get_post_link_selector() -> str:
    """Get selector for post link."""
    return SELECTORS.get_selector_chain(SELECTORS.POST_LINK)
