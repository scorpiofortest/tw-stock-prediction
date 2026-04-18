"""
Global test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

# Import the base model (will be created by backend team)
# from backend.models.database_models import Base
# from backend.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """
    Create an in-memory SQLite database engine for testing.
    Each test gets a fresh database.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.
    Automatically rolls back after each test.
    """
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP test client with database session override.
    """
    # Override the database dependency in FastAPI app
    # app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(base_url="http://test") as client:
        yield client

    # Clear overrides
    # app.dependency_overrides.clear()


@pytest.fixture
def sample_stock_id() -> str:
    """Default stock ID for testing (TSMC)"""
    return "2330"


@pytest.fixture
def sample_stock_name() -> str:
    """Default stock name for testing"""
    return "台積電"


@pytest.fixture
def default_user_id() -> int:
    """Default user ID for testing"""
    return 1


@pytest.fixture
def initial_capital() -> float:
    """Default initial capital for paper trading"""
    return 1_000_000.0


# Trading cost constants
@pytest.fixture
def fee_rate() -> float:
    """Commission fee rate: 0.1425%"""
    return 0.001425


@pytest.fixture
def fee_discount() -> float:
    """Commission fee discount: 60%"""
    return 0.6


@pytest.fixture
def tax_rate() -> float:
    """Transaction tax rate: 0.3% (sell only)"""
    return 0.003


@pytest.fixture
def min_fee() -> float:
    """Minimum commission fee: NT$20"""
    return 20.0
