"""Read-only repository sensors for LLM codebase exploration.

While `RepositoryWorkspace` defines the physical security boundary,
    - what paths the runtime is allowed to touch
    
this module defines the LLM-facing sensors
    - how the model inspects and navigates that workspace.
"""

from __future__ import annotations

from fnmatch import fnmatch
from typing import Self

from pydantic import BaseModel, Field, model_validator

from pocketagent.runtime.tools.base import (
    RuntimeTool, ToolEffect, ToolExecutionError
)

from pocketagent.runtime.tools.repository.workspace import (
    DEFAULT_IGNORED_DIRECTORIES,
    RepositoryWorkspace
)

class ListDirectoryArgs(BaseModel):
    path: str = '.'
    max_entries: int = Field(default=200, ge=1, le=500)

class ListDirectoryTool(RuntimeTool[ListDirectoryArgs]):
    name = "list_directory"
    description = (
        "List files and directories directly inside a specified repository path. "
        "Use this to understand repository structure before reading files."
    )
    effect = ToolEffect.READ_ONLY
    args_model = ListDirectoryArgs
    
    def __init__(self, workspace: RepositoryWorkspace) -> None:
        self._workspace = workspace
        
    async def execute(self, args: ListDirectoryArgs):
        directory = self._workspace.resolve(args.path)
        
        if not directory.exists():
            raise ToolExecutionError(
                code="PATH_NOT_FOUND",
                message=f"Path not found: {args.path}"
            )
        
        if not directory.is_dir():
            raise ToolExecutionError(
                code="NOT_A_DIRECTORY",
                message=f"Not a directory: {args.path}"
            )
        
        visible_children = [child 
                            for child in sorted(
                                    directory.iterdir(),
                                    key=lambda item: item.name.lower()
                                ) if (
                                    child.name not in DEFAULT_IGNORED_DIRECTORIES and
                                    not child.is_symlink()
                                )
                            ]

        truncated = len(visible_children) > args.max_entries
        children = visible_children[:args.max_entries]
        
        entries: list[dict[str, str | int]] = []
        
        for child in children:
            item: dict[str, str | int] = {
                "name": child.name,
                "type": "directory" if child.is_dir() else "file"
            }
            
            if child.is_file():
                item["size_bytes"] = child.stat().st_size
            
            entries.append(item)
        
        return {
            "path": args.path,
            "entries": entries,
            "truncated": truncated
        }