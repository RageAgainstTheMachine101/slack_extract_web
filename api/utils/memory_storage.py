"""
In-memory storage for Vercel serverless environment.
This module provides an alternative to filesystem storage when running on Vercel.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# In-memory storage dictionaries
jobs_storage: Dict[str, Any] = {}
extracts_storage: Dict[str, Any] = {}

def save_to_memory(storage_dict: Dict[str, Any], key: str, data: Any) -> str:
    """Save data to in-memory storage and return a virtual path."""
    storage_dict[key] = data
    logger.info(f"Saved data to in-memory storage with key: {key}")
    return f"memory://{key}"

def load_from_memory(storage_dict: Dict[str, Any], key: str) -> Optional[Any]:
    """Load data from in-memory storage."""
    if key not in storage_dict:
        logger.error(f"Key not found in in-memory storage: {key}")
        return None
    
    logger.info(f"Loaded data from in-memory storage with key: {key}")
    return storage_dict[key]

def save_job_data_to_memory(job_id: str, data: Any) -> str:
    """Save job data to in-memory storage."""
    return save_to_memory(jobs_storage, job_id, data)

def load_job_data_from_memory(job_id: str) -> Optional[Any]:
    """Load job data from in-memory storage."""
    return load_from_memory(jobs_storage, job_id)

def save_extract_data_to_memory(extract_id: str, data: Any) -> str:
    """Save extract data to in-memory storage."""
    return save_to_memory(extracts_storage, extract_id, data)

def load_extract_data_from_memory(extract_id: str) -> Optional[Any]:
    """Load extract data from in-memory storage."""
    return load_from_memory(extracts_storage, extract_id)

def clear_memory_storage() -> None:
    """Clear all in-memory storage (useful for testing)."""
    jobs_storage.clear()
    extracts_storage.clear()
    logger.info("Cleared all in-memory storage")
