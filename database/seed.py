import sys
import os
import asyncio

# Adjust python path to load roots properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from models.country import Country

# 8 Target Countries
COUNTRIES_SEED = [
    {"code": "KR", "name": "South Korea"},
    {"code": "US", "name": "United States"},
    {"code": "JP", "name": "Japan"},
    {"code": "IN", "name": "India"},
    {"code": "GB", "name": "United Kingdom"},
    {"code": "CA", "name": "Canada"},
    {"code": "AU", "name": "Australia"},
    {"code": "GLOBAL", "name": "Global Trend"}
]

async def seed_countries() -> None:
    """
    Populate the countries table with initial metadata.
    Uses async session and prevents duplicates.
    """
    # Initialize TimescaleDB hypertable if applicable before seeding
    from database.connection import init_timescaledb
    await init_timescaledb()
    
    print("Starting database seeding for countries...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for seed in COUNTRIES_SEED:
                query = select(Country).where(Country.code == seed["code"])
                result = await session.execute(query)
                exists = result.scalar_one_or_none()
                
                if not exists:
                    country = Country(code=seed["code"], name=seed["name"], is_active=True)
                    session.add(country)
                    print(f"Seeded country: {seed['code']} ({seed['name']})")
                else:
                    print(f"Country {seed['code']} already exists. Skipping.")
        
        await session.commit()
    print("Database seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_countries())

