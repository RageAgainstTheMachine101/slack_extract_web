import os
import logging
from fastapi import APIRouter, HTTPException, Response, Depends, Header
from fastapi.responses import FileResponse, PlainTextResponse
from typing import Dict, Any, Optional

from api.auth.password_auth import verify_password
from api.utils.helpers import is_vercel_environment
from api.utils.memory_storage import load_extract_data_from_memory

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/files/{file_id}")
async def get_file(
    file_id: str, 
    user: Dict[str, Any] = Depends(verify_password),
    x_api_password: Optional[str] = Header(None, alias="X-API-Password")
):
    """
    Serve an extracted file by its ID.
    Requires authentication with a valid API password in the X-API-Password header.
    """
    logger.info(f"File request for {file_id} by authenticated user {user.get('sub')}")
    
    # Double-check that we have the API password header (belt and suspenders approach)
    if not x_api_password:
        logger.error("X-API-Password header is missing in the request")
        raise HTTPException(status_code=401, detail="API password header missing")
    
    try:
        if is_vercel_environment():
            # Use in-memory storage on Vercel
            logger.info(f"Using in-memory storage to retrieve file {file_id}")
            content = load_extract_data_from_memory(file_id)
            if content is None:
                logger.error(f"File {file_id} not found in memory storage")
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")
            
            logger.info(f"Successfully retrieved file {file_id} from memory storage")
            # Return the content as a plain text response
            return PlainTextResponse(
                content=content,
                headers={"Content-Disposition": f"attachment; filename=slack_messages_{file_id}.txt"}
            )
        else:
            # Use filesystem storage locally
            file_path = f"extracts/{file_id}.txt"
            
            if not os.path.exists(file_path):
                logger.error(f"File {file_path} not found in filesystem")
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")
            
            logger.info(f"Successfully retrieved file {file_id} from filesystem")
            return FileResponse(
                path=file_path,
                filename=f"slack_messages_{file_id}.txt",
                media_type="text/plain"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Unexpected error retrieving file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")
