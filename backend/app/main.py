"""
Repository Code Dumper - FastAPI Backend Application

This is the main entry point for the backend API.
"""

import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .validators import validate_github_url, URLValidationError
from .repo_processor import RepoProcessor, RepoProcessorError
from .models import (
    ProcessRepoRequest, 
    ProcessRepoResponse, 
    FileInfo,
    ErrorDetail,
    ErrorResponse,
    HealthCheckResponse,
)
from .config import (
    ALLOWED_ORIGINS,
    MAX_RESPONSE_SIZE,
)
from .middleware import (
    RequestTrackingMiddleware,
    APIKeyAuthMiddleware,
    RateLimitMiddleware,
    REQUEST_ID_HEADER,
)

# Output directory for generated files
# Use environment variable, or fallback to a local 'outputs' directory for development
_default_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
OUTPUT_DIR = Path(os.environ.get('OUTPUT_DIR', _default_output_dir))

try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fallback to temp directory if we can't create the output directory
    import tempfile
    OUTPUT_DIR = Path(tempfile.gettempdir()) / 'repo_dumper_outputs'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Track processing jobs
processing_jobs = {}


def get_request_id(request: Request) -> str:
    """Get request ID from request state or generate a new one."""
    if hasattr(request.state, 'request_id'):
        return request.state.request_id
    return str(uuid.uuid4())


def create_error_response(
    error_code: str,
    error_type: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[dict] = None
) -> dict:
    """Create a standardized error response."""
    return {
        "status": "error",
        "error": {
            "error_code": error_code,
            "error_type": error_type,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


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

# Add middleware in order (last added = first executed)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyAuthMiddleware)
app.add_middleware(RequestTrackingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER, "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Window"],
)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom exception handler to standardize error responses."""
    request_id = get_request_id(request)
    
    # If the detail is already a dict (from our middleware), use it
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        error_detail = exc.detail
        error_detail["request_id"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "error": error_detail},
            headers={REQUEST_ID_HEADER: request_id},
        )
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
    }
    
    error_type_map = {
        400: "validation_error",
        401: "authentication_error",
        403: "authorization_error",
        404: "not_found_error",
        422: "validation_error",
        429: "rate_limit_error",
        500: "server_error",
    }
    
    error_code = error_code_map.get(exc.status_code, "UNKNOWN_ERROR")
    error_type = error_type_map.get(exc.status_code, "unknown_error")
    message = str(exc.detail) if exc.detail else "An error occurred"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_code,
            error_type=error_type,
            message=message,
            request_id=request_id,
        ),
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.get("/")
async def root():
    """Root endpoint with basic API info."""
    return {"status": "ok", "message": "Repository Code Dumper API is running"}


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Enhanced health check endpoint.
    
    Returns detailed health information including:
    - Git availability
    - Disk space status
    - Output directory writability
    """
    # Check if git is available
    git_available = False
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        git_available = result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        git_available = False
    
    # Check disk space (require at least 100MB free)
    disk_space_ok = False
    free_space_mb = 0
    try:
        stat = shutil.disk_usage(OUTPUT_DIR)
        free_space_mb = stat.free / (1024 * 1024)
        disk_space_ok = free_space_mb > 100
    except Exception:
        disk_space_ok = False
    
    # Check if output directory is writable
    output_dir_writable = False
    try:
        test_file = OUTPUT_DIR / ".health_check_test"
        test_file.touch()
        test_file.unlink()
        output_dir_writable = True
    except Exception:
        output_dir_writable = False
    
    # Determine overall status
    is_healthy = git_available and disk_space_ok and output_dir_writable
    
    return HealthCheckResponse(
        status="healthy" if is_healthy else "unhealthy",
        git_available=git_available,
        disk_space_ok=disk_space_ok,
        output_dir_writable=output_dir_writable,
        version="1.0.0",
        details={
            "free_space_mb": round(free_space_mb, 2),
            "output_dir": str(OUTPUT_DIR),
        }
    )


@app.post("/process-repo", response_model=ProcessRepoResponse)
async def process_repository(request_body: ProcessRepoRequest, request: Request):
    """
    Process a GitHub repository and generate a code dump file.
    
    Args:
        request_body: ProcessRepoRequest with repo_url, format, and include_content flag
        request: FastAPI request object for accessing request metadata
        
    Returns:
        ProcessRepoResponse with download URL, file index, and optionally content
    """
    request_id = get_request_id(request)
    
    # Validate URL
    try:
        validated_url = validate_github_url(request_body.repo_url)
    except URLValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                error_code="INVALID_URL",
                error_type="validation_error",
                message=str(e),
                request_id=request_id,
            )["error"]
        )
    
    # Process repository
    try:
        processor = RepoProcessor(validated_url, request_body.format)
        output_file = processor.process(OUTPUT_DIR)
        
        # Get relative path for download URL
        download_url = f"/download/{output_file.name}"
        
        # Build file index from processor metadata
        file_index: List[FileInfo] = [
            FileInfo(
                path=meta["path"],
                language=meta["language"],
                line_count=meta["line_count"],
                size_bytes=meta["size_bytes"],
                status=meta["status"],
            )
            for meta in processor.file_metadata
        ]
        
        # Optionally include content
        content = None
        if request_body.include_content:
            try:
                file_size = output_file.stat().st_size
                if file_size <= MAX_RESPONSE_SIZE:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    # Content too large, don't include it
                    pass
            except Exception:
                # If we can't read the file, just skip content
                pass
        
        return ProcessRepoResponse(
            status="success",
            repo_url=validated_url,
            download_url=download_url,
            message=f"Successfully processed {processor.file_count} files",
            file_count=processor.file_count,
            request_id=request_id,
            file_index=file_index,
            content=content,
        )
        
    except RepoProcessorError as e:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                error_code="PROCESSING_ERROR",
                error_type="processing_error",
                message=str(e),
                request_id=request_id,
            )["error"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code="INTERNAL_ERROR",
                error_type="server_error",
                message=f"Internal error: {str(e)}",
                request_id=request_id,
            )["error"]
        )


@app.get("/download/{filename}")
async def download_file(filename: str, request: Request):
    """
    Download a generated output file.
    
    Args:
        filename: Name of the file to download
        request: FastAPI request object
        
    Returns:
        File response for download
    """
    request_id = get_request_id(request)
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                error_code="INVALID_FILENAME",
                error_type="validation_error",
                message="Invalid filename",
                request_id=request_id,
            )["error"]
        )
    
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                error_code="FILE_NOT_FOUND",
                error_type="not_found_error",
                message="File not found",
                request_id=request_id,
            )["error"]
        )
    
    # Determine media type
    media_type = "text/markdown" if filename.endswith('.md') else "text/plain"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={REQUEST_ID_HEADER: request_id}
    )


@app.delete("/download/{filename}")
async def delete_file(filename: str, request: Request):
    """
    Delete a generated output file.
    
    Args:
        filename: Name of the file to delete
        request: FastAPI request object
        
    Returns:
        Success message
    """
    request_id = get_request_id(request)
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                error_code="INVALID_FILENAME",
                error_type="validation_error",
                message="Invalid filename",
                request_id=request_id,
            )["error"]
        )
    
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                error_code="FILE_NOT_FOUND",
                error_type="not_found_error",
                message="File not found",
                request_id=request_id,
            )["error"]
        )
    
    try:
        file_path.unlink()
        return {
            "status": "success",
            "message": "File deleted",
            "request_id": request_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                error_code="DELETE_ERROR",
                error_type="server_error",
                message=f"Failed to delete file: {str(e)}",
                request_id=request_id,
            )["error"]
        )
