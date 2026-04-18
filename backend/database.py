"""Database engine and session management (SQLAlchemy 2.0 async)."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database():
    """Create all tables and enable WAL mode for SQLite."""
    from models.database_models import Base

    async with engine.begin() as conn:
        # Enable WAL mode for SQLite
        if "sqlite" in settings.DATABASE_URL:
            await conn.execute(
                __import__("sqlalchemy").text("PRAGMA journal_mode=WAL")
            )
            await conn.execute(
                __import__("sqlalchemy").text("PRAGMA foreign_keys=ON")
            )
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """Dispose of the engine."""
    await engine.dispose()


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
