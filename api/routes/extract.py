import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import date

from api.models.schemas import ExtractRequest, ExtractResponse
from api.services.slack_extract import SlackExtractService
from api.utils.helpers import load_job_data, generate_job_id, save_job_data, is_vercel_environment, save_extract_data
from api.auth.password_auth import verify_password

router = APIRouter()
logger = logging.getLogger(__name__)

def get_extract_service():
    return SlackExtractService()

@router.post("/extract", response_model=ExtractResponse)
async def extract_messages(
    request: ExtractRequest,
    extract_service: SlackExtractService = Depends(get_extract_service),
    user: Dict[str, Any] = Depends(verify_password)
) -> Dict[str, Any]:
    """
    Extract and format previously downloaded messages, optionally filtering by date.
    Requires authentication with a valid API password in the X-API-Password header.
    """
    logger.info(f"Extract request for job {request.job_id} by authenticated user {user.get('sub')}")
    
    try:
        # Load the job data
        job_data = load_job_data(request.job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job ID {request.job_id} not found")
        
        # Get messages from the job data
        messages = job_data.get("messages", [])
        if not messages:
            return {
                "status": "success",
                "extracted_message_count": 0,
                "messages": []
            }
        
        # Parse string dates to date objects if provided
        start_date = None
        end_date = None
        
        if request.start_date:
            try:
                start_date = date.fromisoformat(request.start_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid start date format: {str(e)}")
                
        if request.end_date:
            try:
                end_date = date.fromisoformat(request.end_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid end date format: {str(e)}")
        
        # Extract and format messages
        formatted_messages, count = extract_service.extract_messages(
            messages,
            start_date,
            end_date
        )
        
        # Create a unique file name for this extraction
        extract_id = generate_job_id()
        
        # Create file path (will be used differently based on environment)
        file_path = f"extracts/{extract_id}.txt"
        
        # Create extracts directory if we're not on Vercel
        if not is_vercel_environment():
            os.makedirs('extracts', exist_ok=True)
        
        # Save the formatted messages to a file or memory
        extract_service.save_to_file(formatted_messages, file_path)
        
        # Return the response
        return {
            "status": "success",
            "extracted_message_count": count,
            "output_file_url": f"/api/files/{extract_id}",
            "output_content_url": f"/api/files/{extract_id}/content",  
            "messages": formatted_messages[:10] if count > 0 else []  
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error extracting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting messages: {str(e)}")
