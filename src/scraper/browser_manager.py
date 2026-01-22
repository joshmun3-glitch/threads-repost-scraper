"""Browser management using Playwright."""

import json
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

from ..utils.config import BrowserConfig
from ..utils.logger import get_logger
from ..utils.exceptions import NavigationError


logger = get_logger(__name__)


class BrowserManager:
    """Manages Playwright browser lifecycle and session persistence."""

    def __init__(self, config: BrowserConfig, session_file: Optional[Path] = None):
        """
        Initialize browser manager.

        Args:
            config: Browser configuration
            session_file: Path to save/load session state
        """
        self.config = config
        self.session_file = session_file
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def launch(self) -> Browser:
        """
        Launch Playwright browser.

        Returns:
            Browser instance
        """
        logger.info(f"Launching browser (headless={self.config.headless})")

        self.playwright = await async_playwright().start()

        # Launch Chromium with anti-detection measures
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        logger.debug("Browser launched successfully")
        return self.browser

    async def create_context(self, load_session: bool = True) -> BrowserContext:
        """
        Create a new browser context with optional session loading.

        Args:
            load_session: Whether to load saved session state

        Returns:
            BrowserContext instance
        """
        if not self.browser:
            await self.launch()

        # Check if we should load session
        session_state = None
        if load_session and self.session_file and self.session_file.exists():
            try:
                logger.info(f"Loading session from {self.session_file}")
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_state = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")
                session_state = None

        # Create context with configuration
        context_options = {
            'viewport': self.config.viewport,
            'user_agent': self.config.user_agent or await self._get_default_user_agent(),
        }

        if session_state:
            context_options['storage_state'] = session_state

        self.context = await self.browser.new_context(**context_options)

        # Set default timeout
        self.context.set_default_timeout(self.config.timeout)

        # Add anti-detection measures
        await self._apply_stealth(self.context)

        logger.debug("Browser context created")
        return self.context

    async def save_session(self) -> None:
        """Save current session state to file."""
        if not self.context or not self.session_file:
            logger.warning("Cannot save session: no context or session file")
            return

        try:
            # Ensure parent directory exists
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            # Save storage state
            session_state = await self.context.storage_state()

            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_state, f, indent=2)

            logger.info(f"Session saved to {self.session_file}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        logger.debug("Closing browser")

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Browser closed")

    async def _get_default_user_agent(self) -> str:
        """Get a realistic user agent string."""
        # Use Playwright's default user agent
        if self.browser:
            context = await self.browser.new_context()
            page = await context.new_page()
            user_agent = await page.evaluate('navigator.userAgent')
            await page.close()
            await context.close()
            return user_agent

        # Fallback user agent
        return (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

    async def _apply_stealth(self, context: BrowserContext) -> None:
        """
        Apply stealth techniques to avoid detection.

        Args:
            context: Browser context to apply stealth to
        """
        # Add init script to override navigator properties
        await context.add_init_script("""
            // Overwrite the `navigator.webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // Overwrite the `chrome` property
            window.chrome = {
                runtime: {},
            };

            // Overwrite the `permissions` property
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        logger.debug("Stealth measures applied")

    def is_session_valid(self) -> bool:
        """
        Check if saved session file exists and is valid.

        Returns:
            True if session file exists and appears valid
        """
        if not self.session_file or not self.session_file.exists():
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Basic validation - check if it has cookies or origins
                return 'cookies' in data or 'origins' in data
        except Exception:
            return False
