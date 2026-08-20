"""
Configurable Selenium scraper - CLI entry point.

Usage:
    python main.py --config config.yaml
    python main.py --config config.yaml --output output/results.xlsx
"""
import argparse
import sys

from scraper import ScraperConfig, ScraperEngine


def parse_args():
    parser = argparse.ArgumentParser(description="Run a config-driven Selenium scraper.")
    parser.add_argument(
        "--config", "-c", default="config.yaml", help="Path to the YAML config file."
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Override the output path from the config."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        config = ScraperConfig(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        sys.exit(1)
    except KeyError as exc:
        print(f"Config file is missing a required field: {exc}")
        sys.exit(1)

    engine = ScraperEngine(config)
    df = engine.run()

    if df.empty:
        print("No data was scraped. Check your selectors and start_url.")
        sys.exit(1)

    saved_path = engine.save(df, args.output)
    print(f"Done. {len(df)} rows saved to {saved_path}")


if __name__ == "__main__":
    main()
