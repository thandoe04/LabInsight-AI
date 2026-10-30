"""
Health check and baseline API endpoint tests.
"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Verify unauthenticated health endpoint responds with 200 OK and version."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_security_headers_present(client):
    """Verify OWASP-compliant security response headers are returned on all endpoints."""
    response = await client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "strict-origin-when-cross-origin" in response.headers["referrer-policy"]
    assert "camera=()" in response.headers["permissions-policy"]
    assert "x-request-id" in response.headers
