import os
import pytest
from fastapi import HTTPException
from unittest.mock import patch

from api.auth.password_auth import verify_password, get_api_password


@pytest.mark.asyncio
async def test_get_api_password_success():
    """Test successful API password retrieval."""
    with patch.dict(os.environ, {"API_PASSWORD": "test-password"}):
        password = get_api_password()
        assert password == "test-password"


@pytest.mark.asyncio
async def test_get_api_password_missing():
    """Test error when API password is not configured."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(HTTPException) as excinfo:
            get_api_password()
        assert excinfo.value.status_code == 500
        assert "API password not configured" in excinfo.value.detail


@pytest.mark.asyncio
async def test_verify_password_success():
    """Test successful password verification."""
    with patch.dict(os.environ, {"API_PASSWORD": "test-password"}):
        result = await verify_password(api_key="test-password")
        assert result["authenticated"] is True
        assert result["auth_type"] == "api_password"
        assert result["sub"] == "api_user"


@pytest.mark.asyncio
async def test_verify_password_missing():
    """Test error when password header is missing."""
    with pytest.raises(HTTPException) as excinfo:
        await verify_password(api_key=None)
    assert excinfo.value.status_code == 401
    assert "API password header missing" in excinfo.value.detail


@pytest.mark.asyncio
async def test_verify_password_invalid():
    """Test error when password is invalid."""
    with patch.dict(os.environ, {"API_PASSWORD": "test-password"}):
        with pytest.raises(HTTPException) as excinfo:
            await verify_password(api_key="wrong-password")
        assert excinfo.value.status_code == 401
        assert "Invalid API password" in excinfo.value.detail
