"""Create all tables from the SQLAlchemy models. Run once against a fresh database:

    cd backend && DATABASE_URL=postgresql+asyncpg://... python create_tables.py

No migration framework needed at this scale - if the schema changes later,
either drop and recreate (dev), or hand-write the couple of ALTER TABLE
statements needed (production).
"""
import asyncio

from app.db import models  # noqa: F401  registers all tables on Base.metadata
from app.db.base import Base, engine


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(create_all())
