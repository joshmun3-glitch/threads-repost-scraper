"""Authentication handler for Threads."""

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import Page, BrowserContext

from .browser_manager import BrowserManager
from ..utils.logger import get_logger
from ..utils.exceptions import AuthenticationError


logger = get_logger(__name__)


class AuthHandler:
    """Handles authentication for Threads, including 2FA support."""

    LOGIN_URL = "https://www.threads.net/login"
    SUCCESS_INDICATORS = [
        "/",  # Redirects to home page after successful login
        "/@",  # User profile page
    ]

    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize authentication handler.

        Args:
            browser_manager: BrowserManager instance
        """
        self.browser_manager = browser_manager

    async def authenticate(self, force_login: bool = False) -> BrowserContext:
        """
        Authenticate with Threads, using saved session or manual login.

        Args:
            force_login: Force manual login even if session exists

        Returns:
            Authenticated browser context

        Raises:
            AuthenticationError: If authentication fails
        """
        # Check for existing valid session
        if not force_login and self.browser_manager.is_session_valid():
            logger.info("Found existing session, attempting to reuse")
            context = await self.browser_manager.create_context(load_session=True)

            # Verify session is still valid
            if await self._verify_authentication(context):
                logger.info("Existing session is valid")
                return context
            else:
                logger.warning("Existing session is invalid, proceeding with login")
                await context.close()

        # Need to perform manual login
        logger.info("No valid session found, initiating manual login")
        return await self._manual_login()

    async def _manual_login(self) -> BrowserContext:
        """
        Perform manual login with user interaction.

        Returns:
            Authenticated browser context

        Raises:
            AuthenticationError: If login fails
        """
        # Force headed mode for manual login
        original_headless = self.browser_manager.config.headless
        self.browser_manager.config.headless = False

        try:
            # Create new context without loading session
            context = await self.browser_manager.create_context(load_session=False)
            page = await context.new_page()

            # Navigate to login page
            logger.info(f"Navigating to {self.LOGIN_URL}")
            await page.goto(self.LOGIN_URL, wait_until='load', timeout=60000)

            # Instructions for user
            print("\n" + "="*60)
            print("MANUAL LOGIN REQUIRED")
            print("="*60)
            print("\nA browser window has opened. Please:")
            print("1. Enter your username/email and password")
            print("2. Complete any 2FA challenges if prompted")
            print("3. Wait until you are fully logged in (you'll see the Threads home page)")
            print("\n" + "="*60)
            input("\nPress ENTER after you have successfully logged in...")
            print()

            # Verify login was successful
            if not await self._verify_authentication(context):
                raise AuthenticationError(
                    "Login verification failed. Please ensure you are logged in and try again."
                )

            logger.info("Login successful!")

            # Save session for future use
            await self.browser_manager.save_session()

            return context

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")

        finally:
            # Restore original headless setting
            self.browser_manager.config.headless = original_headless

    async def _verify_authentication(self, context: BrowserContext) -> bool:
        """
        Verify that authentication is valid by checking current state.

        Args:
            context: Browser context to verify

        Returns:
            True if authenticated, False otherwise
        """
        try:
            page = await context.new_page()

            # Navigate to Threads home page
            logger.debug("Verifying authentication status")
            response = await page.goto("https://www.threads.net/", wait_until='load', timeout=30000)

            # Check if we're redirected to login (indicates not authenticated)
            current_url = page.url
            if '/login' in current_url:
                logger.debug("Not authenticated (redirected to login)")
                await page.close()
                return False

            # Check if we can access authenticated content
            # Look for elements that only appear when logged in
            try:
                # Wait for navigation elements that indicate logged-in state
                await page.wait_for_selector('svg[aria-label], a[href="/"]', timeout=5000)
                logger.debug("Authentication verified")
                await page.close()
                return True
            except Exception:
                logger.debug("Could not find authenticated elements")
                await page.close()
                return False

        except Exception as e:
            logger.warning(f"Error verifying authentication: {e}")
            return False

    async def logout(self, context: BrowserContext) -> None:
        """
        Log out from Threads and clear session.

        Args:
            context: Browser context to logout from
        """
        try:
            logger.info("Logging out from Threads")

            # Clear all cookies and storage
            await context.clear_cookies()

            # Delete session file if it exists
            if self.browser_manager.session_file and self.browser_manager.session_file.exists():
                self.browser_manager.session_file.unlink()
                logger.info("Session file deleted")

            logger.info("Logout successful")

        except Exception as e:
            logger.error(f"Error during logout: {e}")
