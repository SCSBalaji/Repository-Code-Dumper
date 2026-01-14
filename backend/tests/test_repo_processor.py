"""
Unit tests for repository processor module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.repo_processor import (
    is_binary_file,
    should_skip_directory,
    RepoProcessor,
    RepoProcessorError,
    SKIP_DIRECTORIES,
    BINARY_EXTENSIONS
)


class TestIsBinaryFile:
    """Tests for is_binary_file function."""
    
    def test_binary_extension_png(self):
        """Test PNG file is detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"fake image data")
            f.flush()
            assert is_binary_file(Path(f.name)) is True
            os.unlink(f.name)
    
    def test_binary_extension_exe(self):
        """Test EXE file is detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b"fake exe data")
            f.flush()
            assert is_binary_file(Path(f.name)) is True
            os.unlink(f.name)
    
    def test_binary_extension_zip(self):
        """Test ZIP file is detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b"fake zip data")
            f.flush()
            assert is_binary_file(Path(f.name)) is True
            os.unlink(f.name)
    
    def test_text_file_is_not_binary(self):
        """Test text file is not detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
            f.write("This is plain text")
            f.flush()
            assert is_binary_file(Path(f.name)) is False
            os.unlink(f.name)
    
    def test_python_file_is_not_binary(self):
        """Test Python file is not detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("print('hello world')")
            f.flush()
            assert is_binary_file(Path(f.name)) is False
            os.unlink(f.name)
    
    def test_file_with_null_bytes_is_binary(self):
        """Test file with null bytes is detected as binary."""
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as f:
            f.write(b"some text\x00with null bytes")
            f.flush()
            assert is_binary_file(Path(f.name)) is True
            os.unlink(f.name)


class TestShouldSkipDirectory:
    """Tests for should_skip_directory function."""
    
    def test_skip_git_directory(self):
        """Test .git directory is skipped."""
        assert should_skip_directory('.git') is True
    
    def test_skip_node_modules(self):
        """Test node_modules directory is skipped."""
        assert should_skip_directory('node_modules') is True
    
    def test_skip_venv(self):
        """Test venv directory is skipped."""
        assert should_skip_directory('venv') is True
    
    def test_skip_pycache(self):
        """Test __pycache__ directory is skipped."""
        assert should_skip_directory('__pycache__') is True
    
    def test_skip_hidden_directories(self):
        """Test hidden directories (starting with .) are skipped."""
        assert should_skip_directory('.hidden') is True
        assert should_skip_directory('.config') is True
    
    def test_do_not_skip_src(self):
        """Test src directory is not skipped."""
        assert should_skip_directory('src') is False
    
    def test_do_not_skip_lib(self):
        """Test lib directory is not skipped."""
        assert should_skip_directory('lib') is False
    
    def test_do_not_skip_tests(self):
        """Test tests directory is not skipped."""
        assert should_skip_directory('tests') is False


class TestRepoProcessor:
    """Tests for RepoProcessor class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        processor = RepoProcessor("https://github.com/user/repo")
        assert processor.repo_url == "https://github.com/user/repo"
        assert processor.output_format == 'markdown'
    
    def test_init_with_text_format(self):
        """Test initialization with text format."""
        processor = RepoProcessor("https://github.com/user/repo", "text")
        assert processor.output_format == 'text'
    
    def test_process_file_text_content(self):
        """Test processing a text file."""
        processor = RepoProcessor("https://github.com/user/repo")
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            
            result = processor.process_file(Path(f.name), "test.py")
            assert "test.py" in result
            assert "print('hello')" in result
            os.unlink(f.name)
    
    def test_process_file_binary_content(self):
        """Test processing a binary file."""
        processor = RepoProcessor("https://github.com/user/repo")
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # PNG header
            f.flush()
            
            result = processor.process_file(Path(f.name), "image.png")
            assert "image.png" in result
            assert "[BINARY FILE SKIPPED]" in result
            os.unlink(f.name)
    
    def test_process_file_captures_metadata(self):
        """Test that processing a file captures metadata."""
        processor = RepoProcessor("https://github.com/user/repo")
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("line1\nline2\nline3")
            f.flush()
            temp_name = f.name
        
        try:
            processor.process_file(Path(temp_name), "test.py")
            
            assert len(processor.file_metadata) == 1
            metadata = processor.file_metadata[0]
            assert metadata["path"] == "test.py"
            assert metadata["language"] == "python"
            assert metadata["line_count"] == 3
            assert metadata["status"] == "processed"
        finally:
            os.unlink(temp_name)
    
    def test_process_binary_file_captures_metadata(self):
        """Test that processing a binary file captures binary status in metadata."""
        processor = RepoProcessor("https://github.com/user/repo")
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.flush()
            temp_name = f.name
        
        try:
            processor.process_file(Path(temp_name), "image.png")
            
            assert len(processor.file_metadata) == 1
            metadata = processor.file_metadata[0]
            assert metadata["path"] == "image.png"
            assert metadata["status"] == "binary"
        finally:
            os.unlink(temp_name)
    
    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_run):
        """Test successful repository clone."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        processor = RepoProcessor("https://github.com/user/repo")
        
        try:
            path = processor.clone_repository()
            assert path is not None
            assert mock_run.called
            # Verify git clone was called with correct arguments
            call_args = mock_run.call_args[0][0]
            assert 'git' in call_args
            assert 'clone' in call_args
            assert '--depth' in call_args
            assert '1' in call_args
        finally:
            processor.cleanup()
    
    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_run):
        """Test repository clone failure."""
        mock_run.return_value = MagicMock(
            returncode=1, 
            stderr="Repository not found"
        )
        
        processor = RepoProcessor("https://github.com/user/repo")
        
        with pytest.raises(RepoProcessorError) as exc_info:
            processor.clone_repository()
        
        assert "Failed to clone" in str(exc_info.value)
        processor.cleanup()


class TestBinaryExtensions:
    """Tests for binary extension configuration."""
    
    def test_common_image_extensions(self):
        """Test common image extensions are in the list."""
        assert '.png' in BINARY_EXTENSIONS
        assert '.jpg' in BINARY_EXTENSIONS
        assert '.gif' in BINARY_EXTENSIONS
        assert '.svg' in BINARY_EXTENSIONS
    
    def test_common_archive_extensions(self):
        """Test common archive extensions are in the list."""
        assert '.zip' in BINARY_EXTENSIONS
        assert '.tar' in BINARY_EXTENSIONS
        assert '.gz' in BINARY_EXTENSIONS
    
    def test_common_executable_extensions(self):
        """Test common executable extensions are in the list."""
        assert '.exe' in BINARY_EXTENSIONS
        assert '.dll' in BINARY_EXTENSIONS
        assert '.so' in BINARY_EXTENSIONS


class TestSkipDirectories:
    """Tests for skip directories configuration."""
    
    def test_common_skip_directories(self):
        """Test common directories are in skip list."""
        assert '.git' in SKIP_DIRECTORIES
        assert 'node_modules' in SKIP_DIRECTORIES
        assert 'venv' in SKIP_DIRECTORIES
        assert '__pycache__' in SKIP_DIRECTORIES
