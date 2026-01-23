"""Markdown exporter for Threads reposts."""

from datetime import datetime
from pathlib import Path
from typing import List

from .formatter import MarkdownFormatter
from ..parsers.post_parser import RepostData
from ..utils.config import ScraperResult
from ..utils.logger import get_logger
from ..utils.exceptions import ExportError
from ..utils.validators import sanitize_filename


logger = get_logger(__name__)


class MarkdownExporter:
    """Exports scraped reposts to markdown format for Obsidian."""

    def __init__(self, output_dir: Path):
        """
        Initialize markdown exporter.

        Args:
            output_dir: Directory to save markdown files
        """
        self.output_dir = Path(output_dir)
        self.formatter = MarkdownFormatter()

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, result: ScraperResult) -> Path:
        """
        Export scraper results to a markdown file.

        Args:
            result: ScraperResult containing reposts and metadata

        Returns:
            Path to the created markdown file

        Raises:
            ExportError: If export fails
        """
        try:
            logger.info(f"Exporting {len(result.reposts)} reposts to markdown")

            # Generate filename
            filename = self._generate_filename(result.username, result.scrape_timestamp)
            filepath = self.output_dir / filename

            # Generate markdown content
            content = self._generate_markdown_content(result)

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Markdown file created: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to export markdown: {e}")
            raise ExportError(f"Export failed: {e}")

    def _generate_filename(self, username: str, timestamp: str) -> str:
        """
        Generate a unique filename for the markdown file.

        Args:
            username: Username being scraped
            timestamp: Timestamp string

        Returns:
            Sanitized filename with timestamp
        """
        # Parse timestamp if it's a string
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except Exception:
                dt = datetime.now()
        else:
            dt = timestamp

        # Include date and time for unique filename each run
        datetime_str = dt.strftime("%Y%m%d_%H%M%S")
        base_name = f"threads_reposts_@{username}_{datetime_str}.md"

        return sanitize_filename(base_name)

    def _generate_markdown_content(self, result: ScraperResult) -> str:
        """
        Generate full markdown document content.

        Args:
            result: ScraperResult to convert to markdown

        Returns:
            Complete markdown document as string
        """
        sections = []

        # Parse scrape timestamp
        if isinstance(result.scrape_timestamp, str):
            try:
                scrape_date = datetime.fromisoformat(result.scrape_timestamp.replace('Z', '+00:00'))
            except Exception:
                scrape_date = datetime.now()
        else:
            scrape_date = result.scrape_timestamp

        # 1. YAML frontmatter
        frontmatter = self.formatter.create_yaml_frontmatter(
            title=f"Threads Reposts - @{result.username}",
            username=result.username,
            total_count=result.total_count,
            scrape_date=scrape_date,
            success_count=result.success_count,
            failed_count=result.failed_count,
            new_count=result.new_count,
            duplicate_count=result.duplicate_count
        )
        sections.append(frontmatter)

        # 2. Document header
        header = self.formatter.create_document_header(
            username=result.username,
            total_count=result.total_count,
            scrape_date=scrape_date
        )
        sections.append(header)

        # 3. Summary section (if there are errors or duplicates)
        if result.errors or result.duplicate_count > 0:
            summary = self._generate_summary_section(result)
            sections.append(summary)

        # 4. Individual repost sections
        reposts_content = self._generate_reposts_sections(result.reposts)
        sections.append(reposts_content)

        # 5. Footer
        footer = self._generate_footer(scrape_date)
        sections.append(footer)

        return '\n'.join(sections)

    def _generate_summary_section(self, result: ScraperResult) -> str:
        """Generate a summary section with statistics and errors."""
        lines = [
            "## Summary",
            "",
            f"- **New reposts in this file**: {result.total_count}",
            f"- **Successfully parsed**: {result.success_count}",
            f"- **Failed/Deleted**: {result.failed_count}",
        ]

        # Add duplicate info if any
        if result.duplicate_count > 0:
            lines.append(f"- **Duplicates (skipped)**: {result.duplicate_count}")
            lines.append("")
            lines.append(f"_Note: {result.duplicate_count} repost(s) were already scraped in previous runs and excluded from this file._")

        lines.append("")

        if result.errors:
            lines.append("### Errors Encountered")
            lines.append("")
            for i, error in enumerate(result.errors[:10], 1):  # Show max 10 errors
                lines.append(f"{i}. {error}")
            if len(result.errors) > 10:
                lines.append(f"... and {len(result.errors) - 10} more errors")
            lines.append("")

        lines.append("---")
        lines.append("")

        return '\n'.join(lines)

    def _generate_reposts_sections(self, reposts: List[RepostData]) -> str:
        """Generate sections for all reposts."""
        if not reposts:
            return "## Reposts\n\nNo reposts found.\n"

        sections = ["# Reposts", ""]

        # Sort reposts by timestamp (newest first)
        sorted_reposts = sorted(
            reposts,
            key=lambda r: r.timestamp if r.timestamp else datetime.min,
            reverse=True
        )

        # Generate section for each repost
        for repost in sorted_reposts:
            section = self.formatter.format_repost_section(repost, include_metadata=True)
            sections.append(section)

        return '\n'.join(sections)

    def _generate_footer(self, scrape_date: datetime) -> str:
        """Generate document footer."""
        lines = [
            "---",
            "",
            f"*Scraped on {scrape_date.strftime('%Y-%m-%d %I:%M %p')} using Threads Repost Scraper*",
            ""
        ]

        return '\n'.join(lines)

    def export_reposts_individually(
        self,
        reposts: List[RepostData],
        username: str,
        output_dir: Path = None
    ) -> List[Path]:
        """
        Export each repost to a separate markdown file.

        Args:
            reposts: List of reposts to export
            username: Username being scraped
            output_dir: Optional output directory (uses self.output_dir if not specified)

        Returns:
            List of paths to created files
        """
        if output_dir is None:
            output_dir = self.output_dir

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        logger.info(f"Exporting {len(reposts)} reposts as individual files")

        for i, repost in enumerate(reposts, 1):
            try:
                # Generate unique filename
                date_str = repost.timestamp.strftime("%Y%m%d_%H%M%S") if repost.timestamp else f"unknown_{i}"
                filename = sanitize_filename(f"{username}_repost_{date_str}.md")
                filepath = output_dir / filename

                # Generate content for single repost
                content = self._generate_single_repost_content(repost, username)

                # Write file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                created_files.append(filepath)

            except Exception as e:
                logger.warning(f"Failed to export individual repost {i}: {e}")

        logger.info(f"Exported {len(created_files)} individual files")
        return created_files

    def _generate_single_repost_content(self, repost: RepostData, username: str) -> str:
        """Generate markdown content for a single repost."""
        sections = []

        # YAML frontmatter
        frontmatter = [
            "---",
            f"title: Repost by @{repost.author_username}",
            f"scraped_user: @{username}",
            f"original_author: @{repost.author_username}",
        ]

        if repost.timestamp:
            frontmatter.append(f"post_date: {repost.timestamp.strftime('%Y-%m-%d')}")

        if repost.post_url:
            frontmatter.append(f"source_url: {repost.post_url}")

        frontmatter.append("tags: [threads, repost]")
        frontmatter.append("---")
        frontmatter.append("")

        sections.append('\n'.join(frontmatter))

        # Repost content
        repost_section = self.formatter.format_repost_section(repost, include_metadata=True)
        sections.append(repost_section)

        return '\n'.join(sections)
