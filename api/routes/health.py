import logging
from fastapi import APIRouter
from typing import Dict, Any

from api.models.schemas import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "version": "0.1.0"}
