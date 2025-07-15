"""
Vault Scanner for discovering markdown files in directories.

Provides filesystem scanning functionality to discover all markdown notes
in a vault directory, respecting hidden files and symbolic links.
"""

import os
from pathlib import Path
from typing import Iterator, List, Set
import logging

logger = logging.getLogger(__name__)


class ScanOptions:
    """Configuration options for vault scanning."""
    
    def __init__(
        self,
        include_extensions: Set[str] = None,
        follow_symlinks: bool = False,
        include_hidden: bool = False,
        max_depth: int = None
    ):
        self.include_extensions = include_extensions or {".md", ".markdown"}
        self.follow_symlinks = follow_symlinks
        self.include_hidden = include_hidden
        self.max_depth = max_depth


class VaultScanner:
    """Discovers markdown files in a vault directory."""
    
    def __init__(self, options: ScanOptions = None):
        self.options = options or ScanOptions()
    
    def scan(self, vault_path: str) -> Iterator[Path]:
        """
        Scan a directory for markdown files.
        
        Args:
            vault_path: Path to the vault directory
            
        Yields:
            Path objects for discovered markdown files
            
        Raises:
            FileNotFoundError: If vault_path doesn't exist
            NotADirectoryError: If vault_path is not a directory
        """
        vault_path = Path(vault_path)
        
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault directory not found: {vault_path}")
        
        if not vault_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {vault_path}")
        
        yield from self._scan_directory(vault_path, current_depth=0)
    
    def _scan_directory(self, directory: Path, current_depth: int = 0) -> Iterator[Path]:
        """Recursively scan directory for markdown files."""
        if self.options.max_depth is not None and current_depth > self.options.max_depth:
            return
        
        try:
            for entry in directory.iterdir():
                full_path = directory / entry.name
                
                # Skip hidden files and directories
                if not self.options.include_hidden and entry.name.startswith('.'):
                    continue
                
                # Handle symbolic links
                if full_path.is_symlink():
                    if not self.options.follow_symlinks:
                        continue
                    try:
                        full_path = full_path.resolve()
                    except Exception as e:
                        logger.warning(f"Failed to resolve symlink {full_path}: {e}")
                        continue
                
                if full_path.is_file():
                    if self._is_markdown_file(full_path):
                        yield full_path
                elif full_path.is_dir():
                    yield from self._scan_directory(full_path, current_depth + 1)
                    
        except PermissionError as e:
            logger.warning(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    def _is_markdown_file(self, file_path: Path) -> bool:
        """Check if a file is a markdown file."""
        # Check extension, case-insensitive
        extension = file_path.suffix.lower()
        return extension in self.options.include_extensions
    
    def scan_files(self, vault_path: str) -> List[Path]:
        """
        Scan all files and return as a list.
        
        Args:
            vault_path: Path to vault directory
            
        Returns:
            List of Path objects for markdown files
        """
        return list(self.scan(vault_path))
    
    def is_vault_directory(self, path: str) -> bool:
        """
        Validate that a path is a vault directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path is a valid directory
        """
        try:
            p = Path(path)
            return p.exists() and p.is_dir()
        except Exception:
            return False
    
    def quick_scan_info(self, vault_path: str) -> dict:
        """
        Get quick summary information about a vault.
        
        Args:
            vault_path: Path to vault directory
            
        Returns:
            Dictionary with scan statistics
        """
        try:
            files = list(self.scan(vault_path))
            total_size = sum(f.stat().st_size for f in files if f.exists())
            
            return {
                'total_files': len(files),
                'total_size_bytes': total_size,
                'vault_path': str(vault_path),
                'first_file': str(files[0]) if files else None
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_files': 0,
                'total_size_bytes': 0,
                'vault_path': str(vault_path),
                'first_file': None
            }