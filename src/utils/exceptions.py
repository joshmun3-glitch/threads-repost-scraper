"""Custom exceptions for Threads Scraper."""


class ThreadsScraperError(Exception):
    """Base exception for all scraper errors."""
    pass


class AuthenticationError(ThreadsScraperError):
    """Raised when authentication fails."""
    pass


class NavigationError(ThreadsScraperError):
    """Raised when navigation to a page fails."""
    pass


class ParsingError(ThreadsScraperError):
    """Raised when parsing post data fails."""
    pass


class ExportError(ThreadsScraperError):
    """Raised when exporting data fails."""
    pass


class ConfigurationError(ThreadsScraperError):
    """Raised when configuration is invalid."""
    pass


class RateLimitError(ThreadsScraperError):
    """Raised when rate limiting is detected."""
    pass
