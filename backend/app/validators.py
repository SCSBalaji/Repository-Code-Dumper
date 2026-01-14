"""
URL Validation module for Repository Code Dumper.
Validates and normalizes GitHub repository URLs.
"""

import re
from urllib.parse import urlparse


class URLValidationError(Exception):
    """Custom exception for URL validation errors."""
    pass


def validate_github_url(url: str) -> str:
    """
    Validate and normalize a GitHub repository URL.
    
    Args:
        url: The repository URL to validate
        
    Returns:
        Normalized GitHub URL
        
    Raises:
        URLValidationError: If the URL is invalid
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("Repository URL is required")
    
    url = url.strip()
    
    # Remove .git suffix if present
    if url.endswith('.git'):
        url = url[:-4]
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        raise URLValidationError("Invalid URL format")
    
    # Check for valid GitHub domain
    valid_domains = ['github.com', 'www.github.com']
    if parsed.netloc not in valid_domains:
        raise URLValidationError("Only GitHub repositories are supported")
    
    # Check scheme
    if parsed.scheme not in ['http', 'https']:
        raise URLValidationError("URL must use HTTP or HTTPS protocol")
    
    # Validate path format (must be /owner/repo)
    path_pattern = r'^/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$'
    if not re.match(path_pattern, parsed.path):
        raise URLValidationError("Invalid repository path. Expected format: https://github.com/owner/repo")
    
    # Normalize to HTTPS
    normalized_url = f"https://github.com{parsed.path}"
    
    return normalized_url


def extract_repo_info(url: str) -> dict:
    """
    Extract owner and repository name from a GitHub URL.
    
    Args:
        url: A validated GitHub repository URL
        
    Returns:
        Dictionary with 'owner' and 'repo' keys
    """
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    
    return {
        'owner': parts[0],
        'repo': parts[1]
    }
