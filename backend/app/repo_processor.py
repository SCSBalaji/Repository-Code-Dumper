"""
Repository Processor module for Repository Code Dumper.
Handles cloning, walking, filtering, and processing repository files.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Tuple, Optional, List, Dict, Any
import logging

from .output_formatter import OutputFormatter, get_language_from_extension
from .config import CLONE_TIMEOUT as CONFIG_CLONE_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories to skip during filesystem walk
SKIP_DIRECTORIES = {
    '.git',
    'node_modules',
    'venv',
    '.venv',
    'env',
    '.env',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.nox',
    '.eggs',
    '*.egg-info',
    'dist',
    'build',
    '.next',
    '.nuxt',
    '.output',
    'vendor',
    'bower_components',
    '.bundle',
    '.cache',
    '.parcel-cache',
    'coverage',
    '.nyc_output',
    '.gradle',
    '.mvn',
    'target',
    'bin',
    'obj',
}

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp', '.tiff', '.tif',
    # Audio/Video
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.ogg', '.webm',
    # Archives
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.jar', '.war', '.ear',
    # Executables
    '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.msi', '.dmg', '.deb', '.rpm',
    # Compiled
    '.pyc', '.pyo', '.class', '.o', '.obj', '.a', '.lib', '.wasm',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    # Fonts
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    # Database
    '.db', '.sqlite', '.sqlite3', '.mdb',
    # Other binary
    '.iso', '.img', '.vmdk', '.qcow2',
    # Lock files (often very long and not useful)
    '.lock',
}

# Maximum file size to process (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Maximum repository size (50MB)
MAX_REPO_SIZE = 50 * 1024 * 1024

# Clone timeout in seconds (use configurable value from config)
CLONE_TIMEOUT = CONFIG_CLONE_TIMEOUT

# Maximum number of files to process
MAX_FILE_COUNT = 5000


class RepoProcessorError(Exception):
    """Custom exception for repository processing errors."""
    pass


def is_binary_file(file_path: Path, check_bytes: int = 8192) -> bool:
    """
    Check if a file is binary by looking for null bytes.
    
    Args:
        file_path: Path to the file
        check_bytes: Number of bytes to check
        
    Returns:
        True if file appears to be binary
    """
    # Check extension first
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    
    # Check for null bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(check_bytes)
            if b'\x00' in chunk:
                return True
    except Exception:
        return True
    
    return False


def should_skip_directory(dir_name: str) -> bool:
    """
    Check if a directory should be skipped during traversal.
    
    Args:
        dir_name: Name of the directory
        
    Returns:
        True if directory should be skipped
    """
    return dir_name in SKIP_DIRECTORIES or dir_name.startswith('.')


def get_directory_size(path: Path) -> int:
    """
    Calculate total size of a directory.
    
    Args:
        path: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total


class RepoProcessor:
    """
    Processes a GitHub repository: clones, walks, and generates output.
    """
    
    def __init__(self, repo_url: str, output_format: str = 'markdown'):
        """
        Initialize the processor.
        
        Args:
            repo_url: Validated GitHub repository URL
            output_format: 'markdown' or 'text'
        """
        self.repo_url = repo_url
        self.output_format = output_format
        self.formatter = OutputFormatter(output_format)
        self.temp_dir: Optional[Path] = None
        self.repo_path: Optional[Path] = None
        self.file_count = 0
        self.processed_files: List[str] = []
        self.file_metadata: List[Dict[str, Any]] = []
    
    def clone_repository(self) -> Path:
        """
        Clone the repository to a temporary directory.
        
        Returns:
            Path to the cloned repository
            
        Raises:
            RepoProcessorError: If cloning fails
        """
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix='repo_dumper_'))
        self.repo_path = self.temp_dir / 'repo'
        
        logger.info(f"Cloning repository: {self.repo_url}")
        
        try:
            # Shallow clone with depth 1
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', self.repo_url, str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=CLONE_TIMEOUT
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise RepoProcessorError(f"Failed to clone repository: {error_msg}")
            
            # Check repository size
            repo_size = get_directory_size(self.repo_path)
            if repo_size > MAX_REPO_SIZE:
                raise RepoProcessorError(
                    f"Repository too large: {repo_size / (1024*1024):.1f}MB exceeds limit of {MAX_REPO_SIZE / (1024*1024):.0f}MB"
                )
            
            logger.info(f"Repository cloned successfully. Size: {repo_size / (1024*1024):.1f}MB")
            return self.repo_path
            
        except subprocess.TimeoutExpired:
            raise RepoProcessorError(f"Clone operation timed out after {CLONE_TIMEOUT} seconds")
        except subprocess.SubprocessError as e:
            raise RepoProcessorError(f"Git operation failed: {str(e)}")
    
    def walk_repository(self) -> Generator[Tuple[Path, str], None, None]:
        """
        Walk the repository and yield file paths with their relative paths.
        
        Yields:
            Tuple of (absolute_path, relative_path)
        """
        if not self.repo_path or not self.repo_path.exists():
            raise RepoProcessorError("Repository not cloned yet")
        
        file_count = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            
            # Filter out directories to skip (modifies dirs in place)
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            # Sort for consistent output
            dirs.sort()
            files.sort()
            
            for filename in files:
                file_path = root_path / filename
                relative_path = file_path.relative_to(self.repo_path)
                
                file_count += 1
                if file_count > MAX_FILE_COUNT:
                    logger.warning(f"File limit reached: {MAX_FILE_COUNT}")
                    return
                
                yield file_path, str(relative_path)
    
    def process_file(self, file_path: Path, relative_path: str) -> str:
        """
        Process a single file and return formatted output.
        
        Args:
            file_path: Absolute path to the file
            relative_path: Relative path from repo root
            
        Returns:
            Formatted file content string
        """
        # Initialize file metadata
        metadata: Dict[str, Any] = {
            "path": relative_path,
            "language": get_language_from_extension(relative_path),
            "line_count": 0,
            "size_bytes": 0,
            "status": "processed"
        }
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            metadata["size_bytes"] = file_size
            if file_size > MAX_FILE_SIZE:
                metadata["status"] = "error"
                self.file_metadata.append(metadata)
                return self.formatter.format_error_file(
                    relative_path, 
                    f"File too large: {file_size / (1024*1024):.1f}MB"
                )
        except Exception as e:
            metadata["status"] = "error"
            self.file_metadata.append(metadata)
            return self.formatter.format_error_file(relative_path, str(e))
        
        # Check if binary
        if is_binary_file(file_path):
            metadata["status"] = "binary"
            self.file_metadata.append(metadata)
            return self.formatter.format_binary_file(relative_path)
        
        # Read and format content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            metadata["line_count"] = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
            self.file_metadata.append(metadata)
            return self.formatter.format_file_content(relative_path, content)
        except Exception as e:
            metadata["status"] = "error"
            self.file_metadata.append(metadata)
            return self.formatter.format_error_file(relative_path, str(e))
    
    def generate_output(self, output_path: Path) -> Path:
        """
        Generate the complete output file.
        
        Args:
            output_path: Directory to save the output file
            
        Returns:
            Path to the generated output file
        """
        if not self.repo_path:
            raise RepoProcessorError("Repository not cloned yet")
        
        # Reset metadata
        self.file_metadata = []
        self.processed_files = []
        
        # Generate unique filename
        import uuid
        output_filename = f"output_{uuid.uuid4().hex[:8]}{self.formatter.get_file_extension()}"
        output_file = output_path / output_filename
        
        # First pass: count files
        file_entries = list(self.walk_repository())
        self.file_count = len(file_entries)
        
        logger.info(f"Processing {self.file_count} files")
        
        # Write output with streaming
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(self.formatter.generate_header(self.repo_url, self.file_count))
            
            # Process each file
            for file_path, relative_path in file_entries:
                formatted_content = self.process_file(file_path, relative_path)
                f.write(formatted_content)
                self.processed_files.append(relative_path)
        
        logger.info(f"Output generated: {output_file}")
        return output_file
    
    def cleanup(self):
        """Remove temporary directory and cloned repository."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Temporary directory cleaned up")
            except Exception as e:
                logger.error(f"Failed to cleanup: {e}")
    
    def process(self, output_path: Path) -> Path:
        """
        Run the complete processing pipeline.
        
        Args:
            output_path: Directory to save the output file
            
        Returns:
            Path to the generated output file
        """
        try:
            self.clone_repository()
            return self.generate_output(output_path)
        finally:
            self.cleanup()
