import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.event_service import EventService

@pytest.mark.asyncio
async def test_process_incoming_event():
    # Arrange: Mock the repository so we don't hit a real database
    mock_repo = MagicMock()
    mock_repo.create_event = AsyncMock(return_value={"id": 1, "type": "page_view"})
    
    service = EventService(repo=mock_repo)
    test_payload = {"type": "page_view", "user_id": "123"}

    # Act
    result = await service.process_incoming_event(test_payload)

    # Assert
    mock_repo.create_event.assert_called_once_with(test_payload)
    assert result["id"] == 1
    assert result["type"] == "page_view"