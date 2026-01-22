"""Basic tests for Threads Scraper components."""

import pytest
from src.utils.validators import validate_username, ValidationError
from src.utils.config import ScraperConfig
from src.exporters.formatter import MarkdownFormatter
from datetime import datetime


class TestValidators:
    """Test username validation."""

    def test_valid_username(self):
        """Test valid username formats."""
        assert validate_username("johndoe") == "johndoe"
        assert validate_username("@johndoe") == "johndoe"
        assert validate_username("john_doe") == "john_doe"
        assert validate_username("john.doe") == "john.doe"

    def test_invalid_username(self):
        """Test invalid username formats."""
        with pytest.raises(ValidationError):
            validate_username("")

        with pytest.raises(ValidationError):
            validate_username(".invalid")

        with pytest.raises(ValidationError):
            validate_username("invalid.")

        with pytest.raises(ValidationError):
            validate_username("invalid..name")


class TestConfig:
    """Test configuration."""

    def test_config_creation(self):
        """Test creating a ScraperConfig."""
        config = ScraperConfig(username="testuser")
        assert config.username == "testuser"
        assert config.headless == True
        assert config.scroll_wait_time == 2
        assert config.max_retries == 3

    def test_config_validation(self):
        """Test config validation."""
        with pytest.raises(ValueError):
            ScraperConfig(username="test", scroll_wait_time=-1)

        with pytest.raises(ValueError):
            ScraperConfig(username="test", log_level="INVALID")


class TestFormatter:
    """Test markdown formatter."""

    def test_format_username(self):
        """Test username formatting."""
        assert MarkdownFormatter.format_username("johndoe") == "@johndoe"
        assert MarkdownFormatter.format_username("@johndoe") == "@johndoe"
        assert MarkdownFormatter.format_username("johndoe", with_at=False) == "johndoe"

    def test_create_wikilink(self):
        """Test wikilink creation."""
        assert MarkdownFormatter.create_wikilink("johndoe") == "[[@johndoe]]"
        assert MarkdownFormatter.create_wikilink("@johndoe") == "[[@johndoe]]"

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        dt = datetime(2026, 1, 23, 15, 30, 0)
        formatted = MarkdownFormatter.format_timestamp(dt)
        assert "2026-01-23" in formatted

        formatted_date = MarkdownFormatter.format_timestamp(dt, date_only=True)
        assert formatted_date == "2026-01-23"

    def test_escape_markdown(self):
        """Test markdown escaping."""
        text = "This has `backticks` and \\backslashes"
        escaped = MarkdownFormatter.escape_markdown(text)
        assert "\\`" in escaped
        assert "\\\\" in escaped


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
