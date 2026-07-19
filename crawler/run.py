import asyncio
import argparse
import sys
import os

# Adjust python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawler.collector import DataCollector

async def main():
    parser = argparse.ArgumentParser(description="YouTube Global Intelligence Platform Crawler CLI")
    parser.add_argument(
        "--country",
        type=str,
        default="all",
        help="Specify country code (e.g. KR, US, JP) or 'all' to run for all target countries."
    )
    args = parser.parse_args()

    collector = DataCollector()

    if args.country == "all":
        print("Starting unified YouTube crawling pipeline for all countries...")
        await collector.run_pipeline()
    else:
        country_code = args.country.upper()
        print(f"Starting YouTube crawling pipeline for country: {country_code}...")
        await collector.collect_for_country(country_code)
    
    print("Crawling run completed.")

if __name__ == "__main__":
    asyncio.run(main())
