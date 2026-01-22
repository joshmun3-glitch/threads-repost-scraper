"""Deduplication utilities for avoiding duplicate scraping."""

import re
from pathlib import Path
from typing import Set, List
from ..utils.logger import get_logger


logger = get_logger(__name__)


class DeduplicationManager:
    """Manages deduplication of scraped posts."""

    def __init__(self, output_dir: Path):
        """
        Initialize deduplication manager.

        Args:
            output_dir: Directory containing markdown files
        """
        self.output_dir = Path(output_dir)
        self.existing_urls: Set[str] = set()

    def load_existing_posts(self, username: str) -> Set[str]:
        """
        Load existing post URLs from previous markdown files.

        Args:
            username: Username to check for existing files

        Returns:
            Set of post URLs that have already been scraped
        """
        logger.info(f"Checking for existing scraped posts for @{username}")

        # Find all markdown files for this username
        pattern = f"threads_reposts_@{username}_*.md"
        existing_files = list(self.output_dir.glob(pattern))

        if not existing_files:
            logger.info(f"No existing files found for @{username}")
            return set()

        logger.info(f"Found {len(existing_files)} existing file(s)")

        # Extract URLs from all files
        all_urls = set()
        for file_path in existing_files:
            urls = self._extract_urls_from_file(file_path)
            all_urls.update(urls)
            logger.debug(f"Loaded {len(urls)} URLs from {file_path.name}")

        logger.info(f"Total existing posts: {len(all_urls)}")
        self.existing_urls = all_urls
        return all_urls

    def _extract_urls_from_file(self, file_path: Path) -> Set[str]:
        """
        Extract post URLs from a markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Set of post URLs found in the file
        """
        urls = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Pattern to match: **Source**: [View on Threads](URL)
            # Matches both www.threads.net and threads.net
            pattern = r'\*\*Source\*\*:\s*\[View on Threads\]\((https?://(?:www\.)?threads\.net/@[^/]+/post/[^)]+)\)'
            matches = re.findall(pattern, content)

            for url in matches:
                # Normalize URL (remove www. for consistency)
                normalized = url.replace('https://www.threads.net', 'https://threads.net')
                urls.add(normalized)

        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")

        return urls

    def is_duplicate(self, post_url: str) -> bool:
        """
        Check if a post URL has already been scraped.

        Args:
            post_url: Post URL to check

        Returns:
            True if post is a duplicate, False otherwise
        """
        if not post_url:
            return False

        # Normalize URL
        normalized = post_url.replace('https://www.threads.net', 'https://threads.net')
        return normalized in self.existing_urls

    def filter_duplicates(self, reposts: List) -> tuple[List, List]:
        """
        Filter out duplicate posts from a list.

        Args:
            reposts: List of RepostData objects

        Returns:
            Tuple of (new_posts, duplicate_posts)
        """
        new_posts = []
        duplicate_posts = []

        for repost in reposts:
            if self.is_duplicate(repost.post_url):
                duplicate_posts.append(repost)
            else:
                new_posts.append(repost)

        logger.info(f"Filtered results: {len(new_posts)} new, {len(duplicate_posts)} duplicates")
        return new_posts, duplicate_posts

    def add_url(self, url: str) -> None:
        """
        Add a URL to the set of existing URLs.

        Args:
            url: Post URL to add
        """
        if url:
            normalized = url.replace('https://www.threads.net', 'https://threads.net')
            self.existing_urls.add(normalized)

    def get_stats(self) -> dict:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'total_existing_posts': len(self.existing_urls),
            'output_directory': str(self.output_dir)
        }
