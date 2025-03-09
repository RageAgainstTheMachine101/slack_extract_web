from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class DownloadRequest(BaseModel):
    user_id: str = Field(..., description="Slack user ID to download messages for")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class DownloadResponse(BaseModel):
    status: str = Field(..., description="Status of the download operation")
    message_count: int = Field(..., description="Number of messages downloaded")
    job_id: str = Field(..., description="Unique identifier for this download job")
    download_location: str = Field(..., description="Where the downloaded data is stored")


class ExtractRequest(BaseModel):
    job_id: str = Field(..., description="Job ID from a previous download operation")
    start_date: Optional[str] = Field(None, description="Optional start date to filter messages")
    end_date: Optional[str] = Field(None, description="Optional end date to filter messages")


class ExtractResponse(BaseModel):
    status: str = Field(..., description="Status of the extraction operation")
    extracted_message_count: int = Field(..., description="Number of messages extracted")
    output_file_url: Optional[str] = Field(None, description="URL to download the extracted messages")
    messages: Optional[list] = Field(None, description="Extracted messages if inline response")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Status of the service")
    version: str = Field("0.1.0", description="Version of the service")
