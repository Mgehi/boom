from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Aiven's free-tier Postgres caps concurrent connections at 20, with no
# managed pooler available at that tier. A small bounded pool - reused
# across warm serverless invocations on the same instance, capped per
# instance - keeps worst-case connection usage predictable instead of
# opening a new connection per request with no ceiling (which is what
# NullPool would do). pool_pre_ping guards against a connection going stale
# while its serverless instance sits frozen between invocations.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=3,
    max_overflow=2,
    pool_timeout=10,
    pool_recycle=300,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
