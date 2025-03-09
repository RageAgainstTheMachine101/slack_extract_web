import os
import logging
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from typing import Dict, Any

from api.auth.password_auth import verify_password
from api.utils.helpers import is_vercel_environment
from api.utils.memory_storage import load_extract_data_from_memory

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/files/{file_id}")
async def get_file(file_id: str, user: Dict[str, Any] = Depends(verify_password)):
    """
    Serve an extracted file by its ID.
    Requires authentication with a valid API password in the X-API-Password header.
    """
    logger.info(f"File request for {file_id} by authenticated user {user.get('sub')}")
    
    if is_vercel_environment():
        # Use in-memory storage on Vercel
        content = load_extract_data_from_memory(file_id)
        if content is None:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Return the content as a plain text response
        return PlainTextResponse(
            content=content,
            headers={"Content-Disposition": f"attachment; filename=slack_messages_{file_id}.txt"}
        )
    else:
        # Use filesystem storage locally
        file_path = f"extracts/{file_id}.txt"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        return FileResponse(
            path=file_path,
            filename=f"slack_messages_{file_id}.txt",
            media_type="text/plain"
        )
