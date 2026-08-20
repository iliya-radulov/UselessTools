"""
Core engine for the configurable Selenium scraper.
"""
import logging
import time
from pathlib import Path

import pandas as pd
import yaml
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scraper")


class ScraperConfig:
    """Loads and validates the YAML configuration file."""

    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self.start_url = raw["start_url"]
        self.headless = raw.get("headless", True)
        self.wait_seconds = raw.get("wait_seconds", 10)
        self.delay_between_pages = raw.get("delay_between_pages", 1.5)
        self.user_agent = raw.get("user_agent")

        self.item_selector = raw["item_selector"]
        self.fields = raw["fields"]  # dict: name -> {selector, attribute}

        pagination = raw.get("pagination", {}) or {}
        self.pagination_enabled = pagination.get("enabled", False)
        self.next_button_selector = pagination.get("next_button_selector")
        self.max_pages = pagination.get("max_pages", 1)

        output = raw.get("output", {}) or {}
        self.output_format = output.get("format", "csv").lower()
        self.output_path = output.get("path", "output/results.csv")


class ScraperEngine:
    """Runs a generic, config-driven Selenium scrape."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.driver = None

    # -- driver lifecycle -------------------------------------------------

    def _build_driver(self):
        options = Options()
        if self.config.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        if self.config.user_agent:
            options.add_argument(f"user-agent={self.config.user_agent}")

        # Selenium 4.6+ auto-resolves the correct chromedriver via Selenium Manager,
        # so no manual driver path/service is required.
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(0)  # we use explicit waits instead

    def _quit_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    # -- scraping logic -----------------------------------------------------

    def _wait_for_items(self):
        WebDriverWait(self.driver, self.config.wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.config.item_selector))
        )

    def _extract_field(self, item_el, field_conf):
        selector = field_conf.get("selector")
        attribute = field_conf.get("attribute", "text")

        try:
            target = item_el if selector in (None, "", ".") else item_el.find_element(
                By.CSS_SELECTOR, selector
            )
        except NoSuchElementException:
            return None

        try:
            if attribute == "text":
                return target.text.strip()
            elif attribute == "href":
                return target.get_attribute("href")
            elif attribute == "src":
                return target.get_attribute("src")
            else:
                return target.get_attribute(attribute)
        except StaleElementReferenceException:
            return None

    def _scrape_current_page(self):
        rows = []
        items = self.driver.find_elements(By.CSS_SELECTOR, self.config.item_selector)
        log.info("Found %d items on current page", len(items))

        for item in items:
            row = {}
            for field_name, field_conf in self.config.fields.items():
                row[field_name] = self._extract_field(item, field_conf)
            rows.append(row)
        return rows

    def _go_to_next_page(self) -> bool:
        """Returns True if navigation to the next page succeeded."""
        if not self.config.next_button_selector:
            return False
        try:
            next_button = self.driver.find_element(
                By.CSS_SELECTOR, self.config.next_button_selector
            )
        except NoSuchElementException:
            return False

        if not next_button.is_enabled() or not next_button.is_displayed():
            return False

        try:
            self.driver.execute_script("arguments[0].click();", next_button)
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to click next-page button: %s", exc)
            return False

        return True

    def run(self) -> pd.DataFrame:
        all_rows = []
        self._build_driver()
        try:
            log.info("Opening %s", self.config.start_url)
            self.driver.get(self.config.start_url)

            page_num = 1
            while True:
                log.info("Scraping page %d", page_num)
                try:
                    self._wait_for_items()
                except TimeoutException:
                    log.warning("No items found on page %d (timed out waiting).", page_num)
                    break

                all_rows.extend(self._scrape_current_page())

                if not self.config.pagination_enabled:
                    break
                if page_num >= self.config.max_pages:
                    log.info("Reached max_pages (%d). Stopping.", self.config.max_pages)
                    break

                time.sleep(self.config.delay_between_pages)
                if not self._go_to_next_page():
                    log.info("No further pages found. Stopping.")
                    break

                page_num += 1
        finally:
            self._quit_driver()

        return pd.DataFrame(all_rows)

    def save(self, df: pd.DataFrame, output_path: str = None):
        output_path = output_path or self.config.output_path
        fmt = self.config.output_format

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "xlsx":
            df.to_excel(out_path, index=False)
        else:
            df.to_csv(out_path, index=False)

        log.info("Saved %d rows to %s", len(df), out_path)
        return out_path
