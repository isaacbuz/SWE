"""
Pytest configuration and shared fixtures
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import your app and models
# from src.main import app
# from src.database import Base, get_db
# from src.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        echo=False,
    )

    # Create tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    # Override the get_db dependency
    # async def override_get_db():
    #     yield db_session

    # app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        # app=app,
        base_url="http://test"
    ) as client:
        yield client

    # app.dependency_overrides.clear()


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis client."""
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock


@pytest.fixture
def mock_agent():
    """Mock agent data."""
    return {
        "id": "agent-test-123",
        "name": "Test Agent",
        "type": "developer",
        "status": "available",
        "capabilities": ["code_generation", "code_review"],
        "metrics": {
            "tasks_completed": 10,
            "success_rate": 0.95,
            "average_time": 1200,
        },
    }


@pytest.fixture
def mock_task():
    """Mock task data."""
    return {
        "id": "task-test-123",
        "title": "Test Task",
        "description": "This is a test task",
        "status": "pending",
        "priority": "medium",
        "assigned_agent": None,
        "estimated_duration": 3600,
        "tags": ["test", "development"],
    }


@pytest.fixture
def mock_user():
    """Mock user data."""
    return {
        "id": "user-test-123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "admin",
    }


@pytest.fixture
def auth_headers():
    """Get authentication headers for testing."""
    # This would typically generate a test JWT token
    return {
        "Authorization": "Bearer test_token_123",
    }


@pytest.fixture
async def authenticated_client(client, auth_headers) -> AsyncClient:
    """Create an authenticated test client."""
    client.headers.update(auth_headers)
    return client
