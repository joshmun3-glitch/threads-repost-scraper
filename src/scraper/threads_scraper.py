"""Main orchestrator for Threads repost scraping."""

from datetime import datetime
from typing import List, Optional
from playwright.async_api import Page

from .browser_manager import BrowserManager
from .auth_handler import AuthHandler
from .scroll_handler import ScrollHandler
from ..parsers.post_parser import PostParser, RepostData
from ..utils.config import ScraperConfig, BrowserConfig, ScraperResult
from ..utils.logger import setup_logger
from ..utils.exceptions import NavigationError, ParsingError
from ..utils.deduplication import DeduplicationManager


class ThreadsScraper:
    """Main scraper orchestrator for Threads reposts."""

    def __init__(self, config: ScraperConfig):
        """
        Initialize the Threads scraper.

        Args:
            config: Scraper configuration
        """
        self.config = config
        self.logger = setup_logger(
            'ThreadsScraper',
            level=config.log_level,
            log_file=None  # Could add log file from config
        )

        # Initialize components
        browser_config = BrowserConfig.from_scraper_config(config)
        self.browser_manager = BrowserManager(browser_config, config.session_file)
        self.auth_handler = AuthHandler(self.browser_manager)

    async def run(self) -> ScraperResult:
        """
        Run the complete scraping workflow.

        Returns:
            ScraperResult with reposts and metadata

        Raises:
            Various exceptions for different failure modes
        """
        self.logger.info(f"Starting scraper for user: @{self.config.username}")

        reposts = []
        errors = []
        duplicate_count = 0
        new_count = 0

        # Initialize deduplication manager (unless skip_dedup is enabled)
        dedup_manager = DeduplicationManager(self.config.output_dir)
        existing_urls = set()

        if not self.config.skip_dedup:
            existing_urls = dedup_manager.load_existing_posts(self.config.username)
            if existing_urls:
                self.logger.info(f"Will skip {len(existing_urls)} already scraped posts")
        else:
            self.logger.info("Force mode: Skipping duplicate checking")

        try:
            # 1. Launch browser
            await self.browser_manager.launch()
            self.logger.info("Browser launched")

            # 2. Authenticate
            context = await self.auth_handler.authenticate()
            self.logger.info("Authentication successful")

            # 3. Create new page
            page = await context.new_page()

            # 4. Navigate to reposts page
            reposts_url = f"https://www.threads.net/@{self.config.username}/reposts"
            self.logger.info(f"Navigating to: {reposts_url}")

            try:
                # Use 'load' instead of 'networkidle' to avoid timeout on continuous network activity
                response = await page.goto(reposts_url, wait_until='load', timeout=60000)

                if not response or response.status >= 400:
                    raise NavigationError(f"Failed to load page: HTTP {response.status if response else 'No response'}")

            except Exception as e:
                raise NavigationError(f"Navigation failed: {e}")

            # Check if page loaded successfully
            if '/login' in page.url:
                raise NavigationError("Redirected to login page - session may be invalid")

            # 5. Wait for initial content to load
            self.logger.info("Waiting for initial content to load...")
            await page.wait_for_timeout(10000)  # Wait 10 seconds for initial load

            # Try a small scroll to trigger lazy loading
            self.logger.info("Pre-scroll to trigger lazy loading...")
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(3000)  # Wait 3 more seconds

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)  # Wait 2 more seconds

            # 6. Perform infinite scroll
            self.logger.info("Starting infinite scroll")
            scroll_count = await ScrollHandler.scroll_to_load_all(
                page,
                wait_time=self.config.scroll_wait_time,
                max_retries=self.config.max_retries
            )
            self.logger.info(f"Scrolling complete: {scroll_count} scrolls")

            # 7. Parse all reposts from the page
            self.logger.info("Parsing reposts")
            all_reposts = await PostParser.parse_page_reposts(page)

            # 8. Filter out duplicates (unless skip_dedup is enabled)
            if not self.config.skip_dedup:
                self.logger.info("Filtering duplicates")
                new_reposts, duplicate_reposts = dedup_manager.filter_duplicates(all_reposts)
                reposts = new_reposts
                duplicate_count = len(duplicate_reposts)
                new_count = len(new_reposts)
            else:
                self.logger.info("Force mode: Using all posts without filtering")
                reposts = all_reposts
                duplicate_count = 0
                new_count = len(all_reposts)

            # 9. Apply max_posts limit if specified (only to new posts)
            if self.config.max_posts and len(reposts) > self.config.max_posts:
                self.logger.info(f"Limiting to {self.config.max_posts} new posts")
                reposts = reposts[:self.config.max_posts]
                new_count = len(reposts)

            # 10. Close page
            await page.close()

        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            errors.append(str(e))
            raise

        finally:
            # 11. Cleanup
            await self.browser_manager.close()
            self.logger.info("Browser closed")

        # Create result
        success_count = len([r for r in reposts if not r.is_deleted])
        result = ScraperResult(
            username=self.config.username,
            reposts=reposts,
            total_count=len(reposts),
            success_count=success_count,
            scrape_timestamp=datetime.now().isoformat(),
            errors=errors,
            duplicate_count=duplicate_count,
            new_count=new_count
        )

        self.logger.info(
            f"Scraping complete: {result.total_count} total, "
            f"{result.success_count} successful, {result.failed_count} failed"
        )

        return result

    async def verify_user_exists(self) -> bool:
        """
        Verify that the username exists on Threads.

        Returns:
            True if user exists, False otherwise
        """
        try:
            await self.browser_manager.launch()
            context = await self.auth_handler.authenticate()
            page = await context.new_page()

            profile_url = f"https://www.threads.net/@{self.config.username}"
            response = await page.goto(profile_url, timeout=15000)

            exists = response and response.status == 200

            await page.close()
            await self.browser_manager.close()

            return exists

        except Exception as e:
            self.logger.error(f"Error verifying user: {e}")
            return False

    async def get_user_profile_info(self) -> dict:
        """
        Get basic profile information for the user.

        Returns:
            Dictionary with profile information
        """
        try:
            await self.browser_manager.launch()
            context = await self.auth_handler.authenticate()
            page = await context.new_page()

            profile_url = f"https://www.threads.net/@{self.config.username}"
            await page.goto(profile_url, wait_until='networkidle', timeout=15000)

            # Extract basic info (this is a simplified version)
            info = {
                'username': self.config.username,
                'url': profile_url,
                'exists': True
            }

            await page.close()
            await self.browser_manager.close()

            return info

        except Exception as e:
            self.logger.error(f"Error getting profile info: {e}")
            return {
                'username': self.config.username,
                'exists': False,
                'error': str(e)
            }
