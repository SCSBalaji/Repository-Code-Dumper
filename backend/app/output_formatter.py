"""
Output Formatter module for Repository Code Dumper.
Handles generation of Markdown and Plain Text output files.
"""

from pathlib import Path
from typing import Generator, Tuple

# Extension to language mapping for code blocks
EXTENSION_LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.fish': 'fish',
    '.ps1': 'powershell',
    '.rb': 'ruby',
    '.php': 'php',
    '.java': 'java',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.scala': 'scala',
    '.go': 'go',
    '.rs': 'rust',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.m': 'objectivec',
    '.mm': 'objectivec',
    '.r': 'r',
    '.R': 'r',
    '.sql': 'sql',
    '.graphql': 'graphql',
    '.gql': 'graphql',
    '.lua': 'lua',
    '.pl': 'perl',
    '.pm': 'perl',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.erl': 'erlang',
    '.hrl': 'erlang',
    '.clj': 'clojure',
    '.cljs': 'clojure',
    '.vim': 'vim',
    '.dockerfile': 'dockerfile',
    '.tf': 'terraform',
    '.hcl': 'hcl',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'ini',
    '.env': 'bash',
    '.vue': 'vue',
    '.svelte': 'svelte',
    '.astro': 'astro',
    '.prisma': 'prisma',
}


def get_language_from_extension(file_path: str) -> str:
    """
    Get the language identifier based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language identifier string or empty string if unknown
    """
    path = Path(file_path)
    
    # Handle special files
    filename = path.name.lower()
    if filename == 'dockerfile':
        return 'dockerfile'
    if filename == 'makefile':
        return 'makefile'
    if filename in ['gemfile', 'rakefile']:
        return 'ruby'
    
    extension = path.suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(extension, '')


class OutputFormatter:
    """
    Handles formatting of repository content into different output formats.
    """
    
    def __init__(self, output_format: str = 'markdown'):
        """
        Initialize the formatter.
        
        Args:
            output_format: 'markdown' or 'text'
        """
        if output_format not in ['markdown', 'text']:
            raise ValueError("Format must be 'markdown' or 'text'")
        self.format = output_format
    
    def get_file_extension(self) -> str:
        """Get the appropriate file extension for the output format."""
        return '.md' if self.format == 'markdown' else '.txt'
    
    def format_file_header(self, relative_path: str) -> str:
        """
        Generate the header for a file section.
        
        Args:
            relative_path: Relative path of the file from repo root
            
        Returns:
            Formatted header string
        """
        if self.format == 'markdown':
            return f"\n## File: {relative_path}\n"
        else:
            return f"\n===== FILE: {relative_path} =====\n"
    
    def format_file_content(self, relative_path: str, content: str) -> str:
        """
        Format a file's content for output.
        
        Args:
            relative_path: Relative path of the file
            content: The file content
            
        Returns:
            Formatted content string
        """
        header = self.format_file_header(relative_path)
        
        if self.format == 'markdown':
            language = get_language_from_extension(relative_path)
            # Use triple backticks for code blocks
            return f"{header}```{language}\n{content}\n```\n"
        else:
            return f"{header}{content}\n"
    
    def format_binary_file(self, relative_path: str) -> str:
        """
        Format a binary file entry (skipped).
        
        Args:
            relative_path: Relative path of the file
            
        Returns:
            Formatted binary file notice
        """
        header = self.format_file_header(relative_path)
        return f"{header}[BINARY FILE SKIPPED]\n"
    
    def format_error_file(self, relative_path: str, error: str) -> str:
        """
        Format an error entry for a file that couldn't be read.
        
        Args:
            relative_path: Relative path of the file
            error: Error message
            
        Returns:
            Formatted error notice
        """
        header = self.format_file_header(relative_path)
        return f"{header}[ERROR READING FILE: {error}]\n"
    
    def generate_header(self, repo_url: str, file_count: int = 0) -> str:
        """
        Generate the output file header.
        
        Args:
            repo_url: The repository URL
            file_count: Number of files processed
            
        Returns:
            Formatted header string
        """
        if self.format == 'markdown':
            return f"""# Repository Code Dump

**Source:** {repo_url}
**Files Processed:** {file_count}

---
"""
        else:
            return f"""========================================
REPOSITORY CODE DUMP
========================================
Source: {repo_url}
Files Processed: {file_count}
========================================

"""
