import asyncio
from database.connection import AsyncSessionLocal
from ranking.engine import RankingEngine

async def run():
    async with AsyncSessionLocal() as session:
        engine = RankingEngine(session)
        await engine.run_global_pipeline()
        await session.commit()

asyncio.run(run())
