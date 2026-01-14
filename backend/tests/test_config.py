"""
Unit tests for configuration module.
"""

import os
import pytest
from unittest.mock import patch


class TestConfigFunctions:
    """Tests for configuration helper functions."""
    
    def test_get_env_int_with_valid_value(self):
        """Test getting an integer from environment."""
        from app.config import get_env_int
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            assert get_env_int("TEST_INT", 10) == 42
    
    def test_get_env_int_with_invalid_value(self):
        """Test getting an integer with invalid value falls back to default."""
        from app.config import get_env_int
        with patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            assert get_env_int("TEST_INT", 10) == 10
    
    def test_get_env_int_with_missing_value(self):
        """Test getting an integer with missing value uses default."""
        from app.config import get_env_int
        with patch.dict(os.environ, {}, clear=True):
            assert get_env_int("MISSING_INT", 10) == 10
    
    def test_get_env_bool_true_values(self):
        """Test getting boolean true values."""
        from app.config import get_env_bool
        for value in ["true", "1", "yes", "on", "TRUE", "True"]:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert get_env_bool("TEST_BOOL", False) is True
    
    def test_get_env_bool_false_values(self):
        """Test getting boolean false values."""
        from app.config import get_env_bool
        for value in ["false", "0", "no", "off"]:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                assert get_env_bool("TEST_BOOL", True) is False
    
    def test_get_env_bool_missing_uses_default(self):
        """Test getting boolean with missing value uses default."""
        from app.config import get_env_bool
        with patch.dict(os.environ, {}, clear=True):
            assert get_env_bool("MISSING_BOOL", True) is True
            assert get_env_bool("MISSING_BOOL", False) is False
    
    def test_get_env_list_with_values(self):
        """Test getting a list from comma-separated values."""
        from app.config import get_env_list
        with patch.dict(os.environ, {"TEST_LIST": "one, two, three"}):
            assert get_env_list("TEST_LIST", []) == ["one", "two", "three"]
    
    def test_get_env_list_with_empty_value(self):
        """Test getting a list with empty value uses default."""
        from app.config import get_env_list
        with patch.dict(os.environ, {"TEST_LIST": ""}):
            assert get_env_list("TEST_LIST", ["default"]) == ["default"]
    
    def test_get_env_list_missing_uses_default(self):
        """Test getting a list with missing value uses default."""
        from app.config import get_env_list
        with patch.dict(os.environ, {}, clear=True):
            assert get_env_list("MISSING_LIST", ["default"]) == ["default"]
