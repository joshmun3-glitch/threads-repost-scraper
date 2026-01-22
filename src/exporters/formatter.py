"""Text formatting utilities for markdown export."""

import re
from datetime import datetime
from typing import Optional

from ..parsers.post_parser import RepostData


class MarkdownFormatter:
    """Formatter for converting repost data to markdown format."""

    @staticmethod
    def format_timestamp(dt: Optional[datetime], date_only: bool = False) -> str:
        """
        Format a datetime object for display.

        Args:
            dt: Datetime to format
            date_only: If True, return only date portion

        Returns:
            Formatted datetime string
        """
        if not dt:
            return "Unknown date"

        if date_only:
            return dt.strftime("%Y-%m-%d")
        else:
            return dt.strftime("%Y-%m-%d %I:%M %p")

    @staticmethod
    def format_date_header(dt: Optional[datetime]) -> str:
        """
        Format a date for use as a section header.

        Args:
            dt: Datetime to format

        Returns:
            Formatted date string for header
        """
        if not dt:
            return "Unknown Date"

        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special markdown characters in text.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for markdown
        """
        if not text:
            return ""

        # Characters that need escaping in markdown
        # Be selective - don't escape everything
        special_chars = {
            '\\': '\\\\',
            '`': '\\`',
            '*': '\\*',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '[': '\\[',
            ']': '\\]',
            '(': '\\(',
            ')': '\\)',
            '#': '\\#',
            '+': '\\+',
            '-': '\\-',
            '.': '\\.',
            '!': '\\!',
        }

        # Only escape if the character is used in a markdown-significant way
        # For now, just escape backticks and backslashes to be safe
        text = text.replace('\\', '\\\\')
        text = text.replace('`', '\\`')

        return text

    @staticmethod
    def format_text_content(text: str, max_length: Optional[int] = None) -> str:
        """
        Format post text content for display.

        Args:
            text: Raw text content
            max_length: Optional maximum length to truncate to

        Returns:
            Formatted text
        """
        if not text:
            return "[No content]"

        # Clean up whitespace
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines

        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."

        return text

    @staticmethod
    def format_username(username: str, with_at: bool = True) -> str:
        """
        Format a username for display.

        Args:
            username: Raw username
            with_at: Whether to include @ prefix

        Returns:
            Formatted username
        """
        if not username:
            return "unknown"

        username = username.strip().lstrip('@')

        if with_at:
            return f"@{username}"
        return username

    @staticmethod
    def create_username_link(username: str) -> str:
        """
        Create a markdown link to a Threads profile.

        Args:
            username: Username (with or without @)

        Returns:
            Markdown link to profile
        """
        clean_username = MarkdownFormatter.format_username(username, with_at=False)
        return f"[@{clean_username}](https://www.threads.net/@{clean_username})"

    @staticmethod
    def create_wikilink(username: str) -> str:
        """
        Create an Obsidian wikilink for a username.

        Args:
            username: Username (with or without @)

        Returns:
            Obsidian wikilink
        """
        clean_username = MarkdownFormatter.format_username(username, with_at=True)
        return f"[[{clean_username}]]"

    @staticmethod
    def format_repost_section(repost: RepostData, include_metadata: bool = True) -> str:
        """
        Format a single repost as a markdown section.

        Args:
            repost: RepostData to format
            include_metadata: Whether to include full metadata

        Returns:
            Formatted markdown section
        """
        lines = []

        # Header with date and author
        date_str = MarkdownFormatter.format_date_header(repost.timestamp)
        wikilink = MarkdownFormatter.create_wikilink(repost.author_username)
        lines.append(f"## {date_str} | {wikilink}")
        lines.append("")

        # Quote block with text content
        text = MarkdownFormatter.format_text_content(repost.text)
        # Add > to each line for blockquote
        quoted_lines = [f"> {line}" if line else ">" for line in text.split('\n')]
        lines.extend(quoted_lines)
        lines.append("")

        # Metadata section
        if include_metadata:
            # Author info
            author_link = MarkdownFormatter.create_username_link(repost.author_username)
            author_display = repost.author_name or repost.author_username
            lines.append(f"**Original Author**: {author_link} ({author_display})")

            # Timestamp
            timestamp_str = MarkdownFormatter.format_timestamp(repost.timestamp)
            lines.append(f"**Post Date**: {timestamp_str}")

            # Post URL
            if repost.post_url:
                lines.append(f"**Source**: [View on Threads]({repost.post_url})")

            # Deleted indicator
            if repost.is_deleted:
                lines.append("**Status**: _Post unavailable or deleted_")

            lines.append("")

        # Divider
        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def create_yaml_frontmatter(
        title: str,
        username: str,
        total_count: int,
        scrape_date: datetime,
        **kwargs
    ) -> str:
        """
        Create YAML frontmatter for Obsidian.

        Args:
            title: Document title
            username: Scraped username
            total_count: Total number of reposts
            scrape_date: Date of scraping
            **kwargs: Additional metadata fields

        Returns:
            YAML frontmatter block
        """
        lines = ["---"]
        lines.append(f"title: {title}")
        lines.append(f"scraped_user: @{username}")
        lines.append(f"scraped_date: {scrape_date.strftime('%Y-%m-%d')}")
        lines.append(f"total_reposts: {total_count}")
        lines.append("tags: [threads, reposts]")

        # Add any additional fields
        for key, value in kwargs.items():
            lines.append(f"{key}: {value}")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def create_document_header(username: str, total_count: int, scrape_date: datetime) -> str:
        """
        Create the document header section.

        Args:
            username: Scraped username
            total_count: Total number of reposts
            scrape_date: Date of scraping

        Returns:
            Markdown header section
        """
        lines = [
            f"# Threads Reposts - @{username}",
            "",
            f"Scraped on: {scrape_date.strftime('%Y-%m-%d %I:%M %p')}",
            f"Total: {total_count} reposts",
            "",
            "---",
            ""
        ]

        return '\n'.join(lines)
