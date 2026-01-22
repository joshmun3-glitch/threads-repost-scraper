# Threads Repost Scraper

A Python-based web scraper that extracts repost data from Threads (Meta's social platform) and exports it to Markdown format for integration with Personal Knowledge Management (PKM) systems like Obsidian.

## Features

- **Browser Automation**: Uses Playwright for reliable web scraping
- **2FA Support**: Manual login workflow supports two-factor authentication
- **Session Persistence**: Saves authentication session to avoid repeated logins
- **Infinite Scroll**: Automatically loads all reposts via infinite scrolling
- **Markdown Export**: Generates Obsidian-compatible markdown files with YAML frontmatter
- **Robust Parsing**: Handles deleted posts, missing data, and edge cases gracefully
- **Configurable**: Command-line arguments for customization

## Requirements

- Python 3.8+
- Windows, macOS, or Linux
- Internet connection
- Threads account (for authentication)

## Installation

### 1. Clone or Download

```bash
git clone <repository-url>
cd thread_scraper
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

## Usage

### Basic Usage

```bash
python -m src.main <username>
```

Example:
```bash
python -m src.main johndoe
```

### First Run (Manual Login)

On your first run, a browser window will open:

1. Enter your Threads username/email and password
2. Complete any 2FA challenges if prompted
3. Wait until you're fully logged in (you'll see the Threads home page)
4. Press ENTER in the terminal

Your session will be saved for future runs.

### Command-Line Options

```bash
python -m src.main <username> [OPTIONS]
```

**Options:**

- `--output-dir <path>`: Directory to save markdown files (default: `output`)
- `--session-file <path>`: Path to session file (default: `session.json`)
- `--headless`: Run browser in headless mode (only works after initial login)
- `--wait-time <seconds>`: Seconds to wait between scrolls (default: 2)
- `--max-retries <number>`: Scroll retries before stopping (default: 3)
- `--max-posts <number>`: Maximum posts to scrape (optional, for testing)
- `--log-level <level>`: Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

### Examples

**Basic scraping:**
```bash
python -m src.main johndoe
```

**Custom output directory:**
```bash
python -m src.main johndoe --output-dir ~/obsidian/inbox
```

**Headless mode (after first login):**
```bash
python -m src.main johndoe --headless
```

**Testing with limited posts:**
```bash
python -m src.main johndoe --max-posts 50 --log-level DEBUG
```

**Slower scrolling for better loading:**
```bash
python -m src.main johndoe --wait-time 5
```

## Output Format

The scraper generates a single markdown file per run:

**Filename:** `threads_reposts_@<username>_<YYYYMMDD>.md`

**Content Structure:**
```markdown
---
title: Threads Reposts - @username
scraped_date: 2026-01-23
total_reposts: 156
tags: [threads, reposts]
---

# Threads Reposts - @username

Scraped on: 2026-01-23 10:30 AM
Total: 156 reposts

---

## 2026-01-22 | [[@author_username]]

> Repost text content here...

**Original Author**: [@author_username](https://threads.net/@author_username) (Display Name)
**Post Date**: 2026-01-22 10:45 AM
**Source**: [View on Threads](https://threads.net/@author/post/ABC123)

---
```

## Obsidian Integration

The generated markdown files are designed for Obsidian:

- **YAML Frontmatter**: Contains metadata (date, author, tags)
- **Wikilinks**: Author usernames formatted as `[[@username]]`
- **External Links**: Direct links to original posts on Threads
- **Tags**: Tagged with `threads` and `reposts` for easy filtering

### Importing to Obsidian

1. Run the scraper with your desired username
2. Copy the generated markdown file from the `output` folder
3. Paste it into your Obsidian vault
4. The file will render with proper formatting and clickable links

## Project Structure

```
thread_scraper/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── scraper/
│   │   ├── threads_scraper.py     # Main orchestrator
│   │   ├── browser_manager.py     # Playwright browser lifecycle
│   │   ├── auth_handler.py        # Login with 2FA support
│   │   └── scroll_handler.py      # Infinite scroll logic
│   ├── parsers/
│   │   ├── post_parser.py         # Extract data from DOM
│   │   └── selectors.py           # CSS/attribute selectors
│   ├── exporters/
│   │   ├── markdown_exporter.py   # Generate markdown files
│   │   └── formatter.py           # Text formatting
│   └── utils/
│       ├── logger.py              # Logging setup
│       ├── config.py              # Configuration
│       ├── validators.py          # Input validation
│       └── exceptions.py          # Custom exceptions
├── output/                         # Generated markdown files
├── logs/                          # Application logs
├── tests/                         # Test files
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Troubleshooting

### Browser doesn't open on first run

- Make sure Playwright is installed: `playwright install chromium`
- Try running without `--headless` flag

### Authentication fails

- Delete `session.json` and try again
- Ensure you complete the login process fully before pressing ENTER
- Check if your account has additional security restrictions

### Not all reposts are loading

- Increase `--wait-time` (e.g., `--wait-time 5`)
- Increase `--max-retries` (e.g., `--max-retries 5`)
- Check your internet connection

### Parsing errors

Threads frequently updates its HTML structure. If you're getting many parsing errors:

1. Open an issue with details
2. The selectors in `src/parsers/selectors.py` may need updating

### Rate limiting

If you're being rate limited:

- Increase `--wait-time` significantly (e.g., `--wait-time 10`)
- Run the scraper during off-peak hours
- Limit the number of posts with `--max-posts`

## Limitations

- **Requires Authentication**: Must log in with a valid Threads account
- **Obfuscated Selectors**: Threads uses dynamically generated CSS classes that may change
- **Rate Limiting**: Excessive requests may trigger rate limiting
- **Public Accounts Only**: Cannot scrape private accounts you don't follow
- **No Real-time Updates**: Manual scraping only, not continuous monitoring

## Development

### Running Tests

```bash
pytest tests/ -v
```

### With Coverage

```bash
pytest --cov=src tests/
```

### Debugging

Run with DEBUG log level for detailed output:

```bash
python -m src.main username --log-level DEBUG
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This tool is for personal use only. Please respect Threads' Terms of Service and rate limits. The authors are not responsible for any misuse or violations of service terms.

## Support

If you encounter issues:

1. Check the Troubleshooting section
2. Review existing issues on GitHub
3. Open a new issue with:
   - Your Python version
   - Full error message
   - Steps to reproduce

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for browser automation
- Uses [colorlog](https://github.com/borntyping/python-colorlog) for colored logging
- Inspired by the need for better PKM integration with social media content
