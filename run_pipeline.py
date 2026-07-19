# -*- coding: utf-8 -*-
"""Run full pipeline: collect all countries + compute rankings."""
import asyncio
import platform
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from crawler.collector import DataCollector
from database.connection import AsyncSessionLocal
from ranking.engine import RankingEngine

async def main():
    # Step 1: Collect data for all countries
    print("=" * 60)
    print("STEP 1: Collecting YouTube trending data for all countries...")
    print("=" * 60)
    collector = DataCollector()
    await collector.run_pipeline()

    # Step 2: Run ranking engine
    print()
    print("=" * 60)
    print("STEP 2: Computing virality scores and rankings...")
    print("=" * 60)
    async with AsyncSessionLocal() as session:
        engine = RankingEngine(session)
        await engine.run_global_pipeline()
        await session.commit()

    # Step 3: Print summary
    print()
    print("=" * 60)
    print("STEP 3: Summary")
    print("=" * 60)
    import sqlite3
    conn = sqlite3.connect("youtube.db")
    cur = conn.cursor()
    print("\n[Videos per Country]")
    for row in cur.execute("""
        SELECT country_code,
               count(*) as total,
               sum(case when isShort=1 then 1 else 0 end) as shorts,
               sum(case when isShort=0 then 1 else 0 end) as longform
        FROM videos GROUP BY country_code ORDER BY country_code
    """).fetchall():
        print(f"  {row[0]}: Total {row[1]} (Longform: {row[3]}, Shorts: {row[2]})")
    
    print("\n[Rankings per Country]")
    for row in cur.execute("""
        SELECT country_code, is_shorts, count(*)
        FROM video_rank GROUP BY country_code, is_shorts ORDER BY country_code
    """).fetchall():
        type_name = "Shorts" if row[1] else "Longform"
        print(f"  {row[0]} [{type_name}]: {row[2]} ranks")
    
    conn.close()
    print("\nDone!")

asyncio.run(main())
