"""
Pytest configuration and shared test fixtures for LabInsight AI backend.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app

settings = get_settings()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test HTTP client talking directly to the FastAPI ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver/api/v1") as ac:
        yield ac
