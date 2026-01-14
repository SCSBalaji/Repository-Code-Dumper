"""
Unit tests for URL validation module.
"""

import pytest
from app.validators import validate_github_url, extract_repo_info, URLValidationError


class TestValidateGitHubURL:
    """Tests for validate_github_url function."""
    
    def test_valid_https_url(self):
        """Test valid HTTPS GitHub URL."""
        url = "https://github.com/owner/repo"
        result = validate_github_url(url)
        assert result == "https://github.com/owner/repo"
    
    def test_valid_url_with_git_suffix(self):
        """Test URL with .git suffix is normalized."""
        url = "https://github.com/owner/repo.git"
        result = validate_github_url(url)
        assert result == "https://github.com/owner/repo"
    
    def test_valid_url_with_trailing_slash(self):
        """Test URL with trailing slash is normalized."""
        url = "https://github.com/owner/repo/"
        result = validate_github_url(url)
        assert result == "https://github.com/owner/repo"
    
    def test_valid_http_url_normalized_to_https(self):
        """Test HTTP URL is normalized to HTTPS."""
        url = "http://github.com/owner/repo"
        result = validate_github_url(url)
        assert result == "https://github.com/owner/repo"
    
    def test_valid_www_url(self):
        """Test www.github.com URL."""
        url = "https://www.github.com/owner/repo"
        result = validate_github_url(url)
        assert result == "https://github.com/owner/repo"
    
    def test_valid_url_with_dashes_and_underscores(self):
        """Test URL with dashes and underscores in names."""
        url = "https://github.com/my-org/my_repo"
        result = validate_github_url(url)
        assert result == "https://github.com/my-org/my_repo"
    
    def test_empty_url_raises_error(self):
        """Test empty URL raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url("")
        assert "required" in str(exc_info.value).lower()
    
    def test_none_url_raises_error(self):
        """Test None URL raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url(None)
        assert "required" in str(exc_info.value).lower()
    
    def test_non_github_domain_raises_error(self):
        """Test non-GitHub domain raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url("https://gitlab.com/owner/repo")
        assert "github" in str(exc_info.value).lower()
    
    def test_invalid_path_format_raises_error(self):
        """Test invalid path format raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url("https://github.com/only-owner")
        assert "invalid" in str(exc_info.value).lower()
    
    def test_deep_path_raises_error(self):
        """Test deep path (more than owner/repo) raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url("https://github.com/owner/repo/extra")
        assert "invalid" in str(exc_info.value).lower()
    
    def test_ftp_scheme_raises_error(self):
        """Test FTP scheme raises validation error."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_github_url("ftp://github.com/owner/repo")
        assert "http" in str(exc_info.value).lower()


class TestExtractRepoInfo:
    """Tests for extract_repo_info function."""
    
    def test_extract_owner_and_repo(self):
        """Test extracting owner and repo from URL."""
        url = "https://github.com/myowner/myrepo"
        result = extract_repo_info(url)
        assert result == {'owner': 'myowner', 'repo': 'myrepo'}
    
    def test_extract_with_dashes(self):
        """Test extracting with dashes in names."""
        url = "https://github.com/my-owner/my-repo"
        result = extract_repo_info(url)
        assert result == {'owner': 'my-owner', 'repo': 'my-repo'}
