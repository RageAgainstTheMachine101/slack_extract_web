import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app


@pytest.fixture
def test_client():
    """Return a TestClient instance for FastAPI app testing."""
    return TestClient(app)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "API_PASSWORD": "test-password"
    }):
        yield
