import os
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Dict, Any

# Create API key header scheme
API_KEY_HEADER = APIKeyHeader(name="X-API-Password", auto_error=False)

def get_api_password() -> str:
    """Get the API password from environment variables."""
    password = os.getenv("API_PASSWORD")
    if not password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API password not configured"
        )
    return password

async def verify_password(api_key: str = Depends(API_KEY_HEADER)) -> Dict[str, Any]:
    """
    Verify the API password from the request header.
    Returns a dict with user info if successful, raises HTTPException if not.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API password header missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    expected_password = get_api_password()
    
    if api_key != expected_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API password",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Return a simple user context (similar to what Supabase auth would return)
    return {
        "authenticated": True,
        "auth_type": "api_password",
        "sub": "api_user"  # Subject identifier
    }
