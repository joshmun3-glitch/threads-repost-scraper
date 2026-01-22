# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based scraper for extracting repost content from Threads (Meta's social platform). The project aims to parse repost data and export it to formats compatible with Personal Knowledge Management (PKM) systems like Obsidian.

## Architecture

The project supports two extraction methods:

### Method 1: JSON Parsing (Primary/Recommended)
- Input: Official data export from Threads (JSON format)
- Process: Parse JSON data to extract repost entries
- Output: Text/Markdown files with repost content, timestamps, and metadata
- Key considerations:
  - JSON structure may vary based on Meta's data export format updates
  - Look for keys like `reposted_post`, `caption`, `creation_timestamp`
  - Data structure might use `media_map` or `reposts` arrays

### Method 2: Web Scraping (Alternative)
- Uses browser automation (Playwright/Selenium)
- Handles authentication and infinite scroll
- Extracts content via CSS selectors
- Note: Threads uses obfuscated class names that change frequently; prefer attribute-based selectors

## Data Flow

1. **Input**: Threads JSON export or live web scraping
2. **Processing**: Extract repost content, timestamps, and metadata
3. **Output**: Markdown files formatted for Obsidian integration

## Development Notes

### JSON Structure Awareness
When working with the JSON parsing method, the exact structure depends on Meta's export format. Always inspect the actual JSON file first to identify:
- Root data structure (array vs object)
- Location of repost indicators
- Timestamp format (Unix timestamp expected)
- Text content field names

### Output Format
Default output should be Markdown for PKM integration:
- Include timestamp in `[YYYY-MM-DD]` format
- Separate entries with visual dividers
- Consider adding YAML frontmatter for Obsidian metadata

### Selectors for Web Scraping
Threads frequently updates CSS classes. When implementing scraping:
- Use `data-*` attributes when available (e.g., `div[data-pressable-container="true"]`)
- Avoid hardcoded class names
- Implement robust error handling for missing elements

## File Naming

Use descriptive Korean/English hybrid naming as needed for user clarity (e.g., `my_reposts.txt`, `리포스트_추출.md`).
