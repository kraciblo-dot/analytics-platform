import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app 
from app.api.deps import get_current_owner
from app.models.tenant import User

client = TestClient(app)

# 1. Create a fake user dependency
async def mock_get_current_owner():
    dummy_user = User()
    dummy_user.organization_id = 123  # Assign a fake org ID
    return dummy_user

@patch("app.api.routers.events.process_event_async.delay")
def test_ingest_event_endpoint(mock_celery_delay):
    # 2. Override the authentication dependency
    app.dependency_overrides[get_current_owner] = mock_get_current_owner

    # 3. Arrange: Format the payload as a batch to match EventBatchCreate
    payload = {
        "events": [
            {
                "event_name": "button_click",
                "timestamp": "2026-05-26T11:55:00Z",
                "properties": {"button_id": "signup"}
            }
        ]
    }

    # Act
    response = client.post("/api/events/ingest", json=payload)

    # 4. Clean up the override so it doesn't pollute other future tests
    app.dependency_overrides.clear()

    # Assert
    assert response.status_code == 202
    assert response.json() == {
        "status": "accepted",
        "message": "Queued 1 events for background processing via Celery",
        "organization_id": 123
    }
    
    mock_celery_delay.assert_called_once()