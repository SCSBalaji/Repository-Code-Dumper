"""
Unit tests for output formatter module.
"""

import pytest
from app.output_formatter import (
    OutputFormatter, 
    get_language_from_extension,
    EXTENSION_LANGUAGE_MAP
)


class TestGetLanguageFromExtension:
    """Tests for get_language_from_extension function."""
    
    def test_python_extension(self):
        """Test Python file extension."""
        assert get_language_from_extension("test.py") == "python"
    
    def test_javascript_extension(self):
        """Test JavaScript file extension."""
        assert get_language_from_extension("test.js") == "javascript"
    
    def test_typescript_extension(self):
        """Test TypeScript file extension."""
        assert get_language_from_extension("test.ts") == "typescript"
    
    def test_tsx_extension(self):
        """Test TSX file extension."""
        assert get_language_from_extension("Component.tsx") == "typescript"
    
    def test_yaml_extension(self):
        """Test YAML file extension."""
        assert get_language_from_extension("config.yaml") == "yaml"
        assert get_language_from_extension("config.yml") == "yaml"
    
    def test_dockerfile(self):
        """Test Dockerfile detection."""
        assert get_language_from_extension("Dockerfile") == "dockerfile"
    
    def test_makefile(self):
        """Test Makefile detection."""
        assert get_language_from_extension("Makefile") == "makefile"
    
    def test_gemfile(self):
        """Test Gemfile detection."""
        assert get_language_from_extension("Gemfile") == "ruby"
    
    def test_unknown_extension(self):
        """Test unknown extension returns empty string."""
        assert get_language_from_extension("file.xyz") == ""
    
    def test_uppercase_extension(self):
        """Test uppercase extension is handled."""
        # Extensions are lowercased internally
        assert get_language_from_extension("README.MD") == "markdown"


class TestOutputFormatter:
    """Tests for OutputFormatter class."""
    
    def test_init_markdown_format(self):
        """Test initialization with markdown format."""
        formatter = OutputFormatter('markdown')
        assert formatter.format == 'markdown'
    
    def test_init_text_format(self):
        """Test initialization with text format."""
        formatter = OutputFormatter('text')
        assert formatter.format == 'text'
    
    def test_init_invalid_format_raises_error(self):
        """Test initialization with invalid format raises error."""
        with pytest.raises(ValueError):
            OutputFormatter('xml')
    
    def test_get_file_extension_markdown(self):
        """Test file extension for markdown format."""
        formatter = OutputFormatter('markdown')
        assert formatter.get_file_extension() == '.md'
    
    def test_get_file_extension_text(self):
        """Test file extension for text format."""
        formatter = OutputFormatter('text')
        assert formatter.get_file_extension() == '.txt'
    
    def test_format_file_header_markdown(self):
        """Test file header formatting for markdown."""
        formatter = OutputFormatter('markdown')
        header = formatter.format_file_header("src/main.py")
        assert "## File: src/main.py" in header
    
    def test_format_file_header_text(self):
        """Test file header formatting for text."""
        formatter = OutputFormatter('text')
        header = formatter.format_file_header("src/main.py")
        assert "===== FILE: src/main.py =====" in header
    
    def test_format_file_content_markdown(self):
        """Test file content formatting for markdown."""
        formatter = OutputFormatter('markdown')
        content = formatter.format_file_content("test.py", "print('hello')")
        assert "## File: test.py" in content
        assert "```python" in content
        assert "print('hello')" in content
        assert "```" in content
    
    def test_format_file_content_text(self):
        """Test file content formatting for text."""
        formatter = OutputFormatter('text')
        content = formatter.format_file_content("test.py", "print('hello')")
        assert "===== FILE: test.py =====" in content
        assert "print('hello')" in content
    
    def test_format_binary_file_markdown(self):
        """Test binary file formatting for markdown."""
        formatter = OutputFormatter('markdown')
        content = formatter.format_binary_file("image.png")
        assert "## File: image.png" in content
        assert "[BINARY FILE SKIPPED]" in content
    
    def test_format_binary_file_text(self):
        """Test binary file formatting for text."""
        formatter = OutputFormatter('text')
        content = formatter.format_binary_file("image.png")
        assert "===== FILE: image.png =====" in content
        assert "[BINARY FILE SKIPPED]" in content
    
    def test_format_error_file(self):
        """Test error file formatting."""
        formatter = OutputFormatter('markdown')
        content = formatter.format_error_file("broken.txt", "Permission denied")
        assert "## File: broken.txt" in content
        assert "[ERROR READING FILE: Permission denied]" in content
    
    def test_generate_header_markdown(self):
        """Test header generation for markdown."""
        formatter = OutputFormatter('markdown')
        header = formatter.generate_header("https://github.com/user/repo", 42)
        assert "# Repository Code Dump" in header
        assert "https://github.com/user/repo" in header
        assert "42" in header
    
    def test_generate_header_text(self):
        """Test header generation for text."""
        formatter = OutputFormatter('text')
        header = formatter.generate_header("https://github.com/user/repo", 42)
        assert "REPOSITORY CODE DUMP" in header
        assert "https://github.com/user/repo" in header
        assert "42" in header
