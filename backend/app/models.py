"""
Data models for Repository Code Dumper API.
Defines request and response schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProcessRepoRequest(BaseModel):
    """Request model for repository processing."""
    repo_url: str = Field(..., description="GitHub repository URL")
    format: str = Field(default="markdown", description="Output format: 'markdown' or 'text'")
    include_content: bool = Field(
        default=False,
        description="If true, includes the full dump content in the response body"
    )
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ['markdown', 'text']:
            raise ValueError("Format must be 'markdown' or 'text'")
        return v


class FileInfo(BaseModel):
    """Information about a single file in the repository."""
    path: str = Field(..., description="Relative path of the file from repository root")
    language: str = Field(default="", description="Detected programming language")
    line_count: int = Field(default=0, description="Number of lines in the file")
    size_bytes: int = Field(default=0, description="Size of the file in bytes")
    status: str = Field(
        default="processed",
        description="Processing status: 'processed', 'binary', or 'error'"
    )


class ProcessRepoResponse(BaseModel):
    """Response model for repository processing."""
    status: str = Field(..., description="Processing status: 'success' or 'error'")
    repo_url: str = Field(..., description="The repository URL that was processed")
    download_url: str = Field(..., description="URL to download the generated file")
    message: Optional[str] = Field(default=None, description="Human-readable status message")
    file_count: Optional[int] = Field(default=None, description="Total number of files processed")
    request_id: Optional[str] = Field(default=None, description="Request tracking identifier")
    file_index: Optional[List[FileInfo]] = Field(
        default=None, 
        description="Structured list of all files with metadata"
    )
    content: Optional[str] = Field(
        default=None, 
        description="Full dump content (only included when include_content=true)"
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    error_code: str = Field(..., description="Machine-readable error code")
    error_type: str = Field(..., description="Category of the error")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request tracking identifier")


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    status: str = Field(default="error", description="Always 'error' for error responses")
    error: ErrorDetail = Field(..., description="Error details")


class HealthCheckResponse(BaseModel):
    """Enhanced health check response model."""
    status: str = Field(..., description="Overall health status: 'healthy' or 'unhealthy'")
    git_available: bool = Field(..., description="Whether git command is available")
    disk_space_ok: bool = Field(..., description="Whether sufficient disk space is available")
    output_dir_writable: bool = Field(..., description="Whether output directory is writable")
    version: str = Field(default="1.0.0", description="API version")
    details: Optional[dict] = Field(default=None, description="Additional health details")
