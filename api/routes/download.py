import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import date

from api.models.schemas import DownloadRequest, DownloadResponse
from api.services.slack_download import SlackDownloadService
from api.utils.helpers import generate_job_id, save_job_data
from api.auth.password_auth import verify_password

router = APIRouter()
logger = logging.getLogger(__name__)

def get_download_service():
    return SlackDownloadService()

@router.post("/download", response_model=DownloadResponse)
async def download_messages(
    request: DownloadRequest,
    download_service: SlackDownloadService = Depends(get_download_service),
    user: Dict[str, Any] = Depends(verify_password)
) -> Dict[str, Any]:
    """
    Download Slack messages for a specified user within a date range.
    Requires authentication with a valid API password in the X-API-Password header.
    """
    logger.info(f"Download request for user {request.user_id} from {request.start_date} to {request.end_date} by authenticated user {user.get('sub')}")
    
    try:
        # Check if SLACK_BOT_TOKEN is available
        if not os.getenv('SLACK_BOT_TOKEN'):
            raise HTTPException(status_code=500, detail="Slack token not configured")
        
        # Check token scopes
        if not download_service.check_token_scopes():
            raise HTTPException(status_code=403, detail="Slack token has insufficient permissions")
        
        # Parse string dates to date objects
        try:
            start_date = date.fromisoformat(request.start_date)
            end_date = date.fromisoformat(request.end_date)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
        
        # Download messages
        result = download_service.download_user_messages(
            request.user_id,
            start_date,
            end_date
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        
        # Generate a job ID and save the data
        job_id = generate_job_id()
        file_path = save_job_data(job_id, result)
        
        # Return the response
        return {
            "status": "success",
            "message_count": result["total_messages"],
            "job_id": job_id,
            "download_location": file_path
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error downloading messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading messages: {str(e)}")
