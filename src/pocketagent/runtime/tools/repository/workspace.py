"""Filesystem boundary & sandbox for repository-analysis tools.

Repository tools (e.g. list_files, read_file, search_code) never access the
host filesystem directly. Instead, they receive a shared RepositoryWorkspace instance
via dependency injection.

Ensures:

1. Path-Traversal & Symlink Jail - reject target that escapes repository root
2. Context-Window & Secret protection - blocks traversal of sensitive directories
3. Uniform security boundary - centralize path validation & directory walking
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from pocketagent.runtime.tools.base import ToolExecutionError

DEFAULT_IGNORED_DIRECTORIES = frozenset({
    ".git", ".venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "dist", "build"
})

class RepositoryWorkspace:
    """Safe repository root exposed to read-only tools"""
    
    # Build RepositoryWorkspace
    def __init__(self, root: str | Path) -> None:
        
        resolved = Path(root).expanduser().resolve()
        
        if not resolved.exists():
            raise ValueError(f"Workspace does not exist: {resolved}")
        
        if not resolved.is_dir():
            raise ValueError(f"Workspace is not a directory: {resolved}")

        self.root = resolved

    # This is different from Path.resolve()
    def resolve(self, relative_path: str) -> Path:
        """Resolve path and reject workspace escape."""
        
        raw_path = Path(relative_path)
        
        if raw_path.is_absolute():
            raise ToolExecutionError(
                code="ABSOLUTE_PATH_NOT_ALLOWED",
                message="Repository tools require relative paths."
            )
        
        candidate = (self.root / raw_path).resolve() # Path.resolve
        
        if not candidate.is_relative_to(self.root):
            raise ToolExecutionError(
                code="PATH_OUTSIDE_WORKSPACE",
                message="Requested path leaves repository workspace.",
                details={
                    "path": relative_path
                }
            )
            
        return candidate

    def display_path(self, path: Path) -> str:
        """Return path relative to repository root."""
        
        return path.relative_to(self.root).as_posix()

    # On-demand scanner for tool to call later
    def iter_files(self, relative_path: str = '.') -> Iterator[Path]:
        """Yield non-ignored files beneath a safe subtree."""
        
        base = self.resolve(relative_path)
        
        if not base.exists():
            raise ToolExecutionError(
                code="PATH_NOT_FOUND",
                message=f"Path does not exist: {relative_path}"
            )
        
        if not base.is_dir():
            raise ToolExecutionError(
                code="NOT_A_DIRECTORY",
                message=f"Expected directory: {relative_path}"
            )
        
        for cur_root, dirs, files in os.walk(base):
            cur = Path(cur_root)
            
            dirs[:] = [dir for dir in dirs if (
                dir not in DEFAULT_IGNORED_DIRECTORIES and not (cur / dir).is_symlink()
            )]
            
            for filename in files:
                path = cur / filename
                
                if path.is_symlink():
                    continue
                
                yield path
        