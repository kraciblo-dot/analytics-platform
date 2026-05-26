import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_owner
from app.api.routers.api_keys import get_api_key_service
from app.models.tenant import User

client = TestClient(app)

# 1. Bypass authentication
async def mock_get_current_owner():
    dummy_user = User()
    dummy_user.organization_id = 123
    return dummy_user

def test_generate_api_key_endpoint():
    # 2. Mock the service layer so we don't hit the database or generate real crypto keys
    mock_service = MagicMock()
    mock_service.create_api_key = AsyncMock(return_value={
        "id": 1,
        "name": "Production Key",
        "raw_key": "sk_live_abc12_def345",
        "prefix": "sk_live_abc12",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # 3. Apply overrides
    app.dependency_overrides[get_current_owner] = mock_get_current_owner
    app.dependency_overrides[get_api_key_service] = lambda: mock_service

    # Arrange
    payload = {
        "name": "Production Key",
        "expires_in_days": 30
    }

    # Act
    response = client.post("/api/keys/", json=payload)

    # Clean up overrides
    app.dependency_overrides.clear()

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Production Key"
    assert data["raw_key"] == "sk_live_abc12_def345"
    assert data["prefix"] == "sk_live_abc12"

    # Verify the service was called with the correct parameters extracted from the payload
    mock_service.create_api_key.assert_called_once_with(
        org_id=123,
        name="Production Key",
        expires_in_days=30
    )