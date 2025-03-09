import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from api.routes import download, extract, files, health

# Load environment variables
load_dotenv(override=True)

# Test comment to verify pre-commit hook functionality
# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create FastAPI app
app = FastAPI(
    title="Slack Extractor API",
    description="API for downloading and extracting Slack messages",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(download.router, prefix="/api", tags=["download"])
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(health.router, prefix="/api", tags=["health"])

# Make sure the required directories exist
os.makedirs('jobs', exist_ok=True)
os.makedirs('extracts', exist_ok=True)
os.makedirs('frontend', exist_ok=True)

# Redirect root to frontend
@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")

# Mount the static files directory for frontend
# This must come after the root route to avoid conflicts
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
