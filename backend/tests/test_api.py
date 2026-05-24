import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_health_check():
    """Ensure the API boots and responds."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "analytics-api"}

@pytest.mark.asyncio
async def test_login_requires_form_data():
    """Ensure our strict OAuth2 schema blocks invalid login attempts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", json={"username": "test@gmail.com", "password": "password"})
    
    # 422 Unprocessable Entity is the correct Pydantic rejection code
    assert response.status_code == 422