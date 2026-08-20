# Configurable Selenium Scraper

A general-purpose web scraper built with Selenium. You point it at a site and
describe what to extract in a YAML config file — no code changes needed for
most sites (unless the site requires logins, heavy JS interaction, or CAPTCHAs).

## Features

- Works on any site: define selectors in a config file instead of code
- Handles pagination (clicks a "next" button across multiple pages)
- Extracts text, links, image URLs, or arbitrary HTML attributes
- Saves results to CSV or Excel (.xlsx)
- Headless by default; can run with a visible browser for debugging

## Requirements

- Python 3.9+
- Google Chrome or Chromium installed on your machine
  (Selenium 4.6+ auto-downloads the matching driver — you don't need to
  install chromedriver yourself)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

1. Copy the example config and edit it for your target site:

   ```bash
   cp config.example.yaml config.yaml
   ```

2. Open your target page in a real browser, right-click the elements you want
   (e.g. a product title), choose "Inspect", and find CSS selectors for:
   - `item_selector`: the repeating container for each row/card/result
   - each `field`: the element *inside* that container holding the value you want
   - `pagination.next_button_selector`: the "next page" button/link, if any

3. Run it:

   ```bash
   python main.py --config config.yaml
   ```

   Optionally override the output path:

   ```bash
   python main.py --config config.yaml --output output/my_results.xlsx
   ```

## Config reference

See `config.example.yaml` for a fully annotated example. Key sections:

| Key | Meaning |
|---|---|
| `start_url` | First page to load |
| `headless` | `true`/`false` — show the browser window or not |
| `item_selector` | CSS selector for each repeating item on the page |
| `fields.<name>.selector` | CSS selector *relative to the item* for one value |
| `fields.<name>.attribute` | `text`, `href`, `src`, or any HTML attribute name |
| `pagination.enabled` | Whether to click through multiple pages |
| `pagination.next_button_selector` | CSS selector for the "next" button |
| `pagination.max_pages` | Safety cap on how many pages to visit |
| `output.format` | `csv` or `xlsx` |
| `output.path` | Where to save the file |

## Tips

- Start with `headless: false` and `max_pages: 1` while you're figuring out
  selectors, so you can watch the browser and confirm it's finding the right
  elements.
- If a field is missing on some items (e.g. no image), it will come back as
  `None` in the output rather than crashing the run.
- Respect the target site's `robots.txt` and terms of service, and add a
  reasonable `delay_between_pages` so you don't hammer their server.
- Sites that require login, solve CAPTCHAs, or load content via complex JS
  interactions (infinite scroll, hover menus) may need small tweaks to
  `scraper/engine.py` — happy to help extend it for a specific case.

## Project structure

```
selenium_scraper/
├── main.py                 # CLI entry point
├── config.example.yaml     # Annotated example config
├── requirements.txt
├── scraper/
│   ├── __init__.py
│   └── engine.py            # Core scraping logic
└── output/                  # Default output folder (created automatically)
```
