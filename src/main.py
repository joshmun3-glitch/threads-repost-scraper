"""CLI entry point for Threads Repost Scraper."""

import argparse
import asyncio
import sys
from pathlib import Path

from .scraper.threads_scraper import ThreadsScraper
from .exporters.markdown_exporter import MarkdownExporter
from .utils.config import ScraperConfig
from .utils.validators import validate_username, ValidationError
from .utils.logger import setup_logger
from .utils.exceptions import ThreadsScraperError


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Threads Repost Scraper - Extract and export reposts from Threads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m src.main johndoe

  # With custom output directory
  python -m src.main johndoe --output-dir ~/obsidian/inbox

  # Limit number of posts (for testing)
  python -m src.main johndoe --max-posts 50

  # Adjust wait time between scrolls
  python -m src.main johndoe --wait-time 3

  # Run in headless mode (after first login)
  python -m src.main johndoe --headless
        """
    )

    # Required arguments
    parser.add_argument(
        'username',
        type=str,
        help='Threads username to scrape (with or without @ prefix)'
    )

    # Optional arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory to save markdown files (default: output)'
    )

    parser.add_argument(
        '--session-file',
        type=str,
        default='session.json',
        help='Path to session file for authentication (default: session.json)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (only works after initial login)'
    )

    parser.add_argument(
        '--wait-time',
        type=int,
        default=2,
        help='Seconds to wait between scrolls (default: 2)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Number of scroll retries before stopping (default: 3)'
    )

    parser.add_argument(
        '--max-posts',
        type=int,
        default=None,
        help='Maximum number of posts to scrape (optional, for testing)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed logging and screenshots'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Threads Repost Scraper v1.0.0'
    )

    return parser.parse_args()


async def main_async():
    """Async main function."""
    # Parse arguments
    args = parse_arguments()

    # Setup logger
    logger = setup_logger('Main', level=args.log_level)

    try:
        # Validate username
        try:
            username = validate_username(args.username)
            logger.info(f"Target username: @{username}")
        except ValidationError as e:
            logger.error(f"Invalid username: {e}")
            sys.exit(1)

        # Create configuration
        config = ScraperConfig(
            username=username,
            output_dir=Path(args.output_dir),
            session_file=Path(args.session_file),
            headless=args.headless,
            scroll_wait_time=args.wait_time,
            max_retries=args.max_retries,
            max_posts=args.max_posts,
            log_level=args.log_level
        )

        logger.debug(f"Configuration: {config}")

        # Print banner
        print("\n" + "="*60)
        print("THREADS REPOST SCRAPER")
        print("="*60)
        print(f"Target User: @{username}")
        print(f"Output Directory: {config.output_dir}")
        print(f"Headless Mode: {config.headless}")
        if config.max_posts:
            print(f"Max Posts: {config.max_posts}")
        print("="*60 + "\n")

        # Initialize scraper
        scraper = ThreadsScraper(config)

        # Run scraping
        logger.info("Starting scraping process")
        result = await scraper.run()

        # Export to markdown (always create a new file with unique timestamp)
        logger.info("Exporting results to markdown")
        exporter = MarkdownExporter(config.output_dir)
        output_file = exporter.export(result)

        # Display summary
        print("\n" + "="*60)
        print("SCRAPING COMPLETE")
        print("="*60)
        print(f"Total reposts found: {result.total_count + result.duplicate_count}")
        print(f"New posts exported: {result.new_count}")
        if result.duplicate_count > 0:
            print(f"Duplicates (skipped from export): {result.duplicate_count}")
        print(f"Successfully parsed: {result.success_count}")
        print(f"Failed/Deleted: {result.failed_count}")
        print(f"\nMarkdown file created: {output_file}")
        if result.new_count == 0:
            print("⚠️  Note: All posts were duplicates, but file was created with unique timestamp")
        print("="*60 + "\n")

        logger.info("Scraping completed successfully")
        return 0

    except ThreadsScraperError as e:
        logger.error(f"Scraper error: {e}")
        print(f"\nError: {e}\n", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        logger.warning("Scraping interrupted by user")
        print("\n\nScraping interrupted by user.\n", file=sys.stderr)
        return 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {e}\n", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted.\n", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
