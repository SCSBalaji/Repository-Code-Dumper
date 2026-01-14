"""
Repository Code Dumper - FastAPI Backend Application

This is the main entry point for the backend API.
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from .validators import validate_github_url, URLValidationError
from .repo_processor import RepoProcessor, RepoProcessorError

# Output directory for generated files
OUTPUT_DIR = Path(os.environ.get('OUTPUT_DIR', '/app/outputs'))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Track processing jobs
processing_jobs = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Startup
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    # Cleanup old output files if needed


app = FastAPI(
    title="Repository Code Dumper",
    description="Clone a GitHub repository and dump all file contents into a single file.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessRepoRequest(BaseModel):
    """Request model for repository processing."""
    repo_url: str = Field(..., description="GitHub repository URL")
    format: str = Field(default="markdown", description="Output format: 'markdown' or 'text'")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ['markdown', 'text']:
            raise ValueError("Format must be 'markdown' or 'text'")
        return v


class ProcessRepoResponse(BaseModel):
    """Response model for repository processing."""
    status: str
    download_url: str
    message: Optional[str] = None
    file_count: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = "error"
    message: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Repository Code Dumper API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/process-repo", response_model=ProcessRepoResponse)
async def process_repository(request: ProcessRepoRequest):
    """
    Process a GitHub repository and generate a code dump file.
    
    Args:
        request: ProcessRepoRequest with repo_url and format
        
    Returns:
        ProcessRepoResponse with download URL
    """
    # Validate URL
    try:
        validated_url = validate_github_url(request.repo_url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Process repository
    try:
        processor = RepoProcessor(validated_url, request.format)
        output_file = processor.process(OUTPUT_DIR)
        
        # Get relative path for download URL
        download_url = f"/download/{output_file.name}"
        
        return ProcessRepoResponse(
            status="success",
            download_url=download_url,
            message=f"Successfully processed {processor.file_count} files",
            file_count=processor.file_count
        )
        
    except RepoProcessorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a generated output file.
    
    Args:
        filename: Name of the file to download
        
    Returns:
        File response for download
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Determine media type
    media_type = "text/markdown" if filename.endswith('.md') else "text/plain"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@app.delete("/download/{filename}")
async def delete_file(filename: str):
    """
    Delete a generated output file.
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Success message
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        file_path.unlink()
        return {"status": "success", "message": "File deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
