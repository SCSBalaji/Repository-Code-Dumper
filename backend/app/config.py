"""
Configuration module for Repository Code Dumper.
Handles environment variable based configuration.
"""

import os
from typing import List, Optional


def get_env_int(key: str, default: int) -> int:
    """Get an integer from environment variable with default."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """Get a boolean from environment variable with default."""
    value = os.environ.get(key, "").lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def get_env_list(key: str, default: List[str]) -> List[str]:
    """Get a comma-separated list from environment variable with default."""
    value = os.environ.get(key)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


# API Authentication
ENABLE_API_AUTH = get_env_bool("ENABLE_API_AUTH", False)
CODE_DUMPER_API_KEY = os.environ.get("CODE_DUMPER_API_KEY", "")

# Rate Limiting
RATE_LIMIT_ENABLED = get_env_bool("RATE_LIMIT_ENABLED", False)
RATE_LIMIT_REQUESTS = get_env_int("RATE_LIMIT_REQUESTS", 100)
RATE_LIMIT_WINDOW = get_env_int("RATE_LIMIT_WINDOW", 60)  # seconds

# Timeouts
CLONE_TIMEOUT = get_env_int("CLONE_TIMEOUT", 120)  # seconds

# Response limits
MAX_RESPONSE_SIZE = get_env_int("MAX_RESPONSE_SIZE", 50 * 1024 * 1024)  # 50MB default

# CORS Configuration
ALLOWED_ORIGINS = get_env_list("ALLOWED_ORIGINS", ["*"])
