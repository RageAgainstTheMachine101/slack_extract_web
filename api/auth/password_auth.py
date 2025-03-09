import os
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Dict, Any

# Create API key header scheme
API_KEY_HEADER = APIKeyHeader(name="X-API-Password", auto_error=False)
logger = logging.getLogger(__name__)

def get_api_password() -> str:
    """Get the API password from environment variables."""
    password = os.getenv("API_PASSWORD")
    if not password:
        logger.error("API_PASSWORD environment variable is not set")
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
        logger.warning("API password header missing in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API password header missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    try:
        expected_password = get_api_password()
        
        if api_key != expected_password:
            logger.warning("Invalid API password provided in request")
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
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Unexpected error in verify_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )
