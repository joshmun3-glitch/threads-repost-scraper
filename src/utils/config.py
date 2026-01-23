"""Configuration management for Threads Scraper."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ScraperConfig:
    """Configuration for the Threads scraper."""

    username: str
    output_dir: Path = field(default_factory=lambda: Path("output"))
    session_file: Path = field(default_factory=lambda: Path("session.json"))
    headless: bool = True
    scroll_wait_time: int = 4  # Increased from 2 to load more content
    max_retries: int = 10  # Increased from 3 to be more aggressive
    max_posts: Optional[int] = None
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate and normalize configuration values."""
        # Convert string paths to Path objects
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.session_file, str):
            self.session_file = Path(self.session_file)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Ensure session file directory exists
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_levels}")
        self.log_level = self.log_level.upper()

        # Validate numeric values
        if self.scroll_wait_time <= 0:
            raise ValueError("scroll_wait_time must be positive")
        if self.max_retries <= 0:
            raise ValueError("max_retries must be positive")
        if self.max_posts is not None and self.max_posts <= 0:
            raise ValueError("max_posts must be positive or None")

    @classmethod
    def from_env(cls, username: str, **overrides) -> 'ScraperConfig':
        """Create configuration from environment variables with optional overrides."""
        config_dict = {
            'username': username,
            'output_dir': os.getenv('OUTPUT_DIR', 'output'),
            'session_file': os.getenv('SESSION_FILE', 'session.json'),
            'headless': os.getenv('HEADLESS', 'true').lower() == 'true',
            'scroll_wait_time': int(os.getenv('SCROLL_WAIT_TIME', '2')),
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }

        # Apply overrides
        config_dict.update(overrides)

        return cls(**config_dict)


@dataclass
class BrowserConfig:
    """Configuration for Playwright browser."""

    headless: bool = True
    viewport: dict = field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None
    timeout: int = 30000  # 30 seconds

    @classmethod
    def from_scraper_config(cls, scraper_config: ScraperConfig) -> 'BrowserConfig':
        """Create browser config from scraper config."""
        return cls(
            headless=scraper_config.headless,
            timeout=scraper_config.scroll_wait_time * 1000 * 2
        )


@dataclass
class ScraperResult:
    """Result of a scraping operation."""

    username: str
    reposts: list
    total_count: int
    success_count: int
    scrape_timestamp: str
    errors: list = field(default_factory=list)
    duplicate_count: int = 0
    new_count: int = 0

    @property
    def failed_count(self) -> int:
        """Number of failed posts."""
        return self.total_count - self.success_count
