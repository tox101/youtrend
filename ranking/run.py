import asyncio
import argparse
import sys
import os

# Adjust python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import AsyncSessionLocal
from ranking.engine import RankingEngine

async def main():
    parser = argparse.ArgumentParser(description="YouTube Global Intelligence Platform Ranking CLI")
    parser.add_argument(
        "--country",
        type=str,
        default="all",
        help="Specify country code (e.g. KR, US, JP) or 'all' to run for all active countries."
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        engine = RankingEngine(session)
        
        if args.country == "all":
            print("Starting global ranking computation for all countries...")
            await engine.run_global_pipeline()
        else:
            country_code = args.country.upper()
            print(f"Starting ranking computation for country: {country_code}...")
            await engine.run_ranking_pipeline_for_country(country_code)
            await session.commit()
            
    print("Ranking run completed.")

if __name__ == "__main__":
    asyncio.run(main())
