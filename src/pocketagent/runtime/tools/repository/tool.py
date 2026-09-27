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

class ReadFileArgs(BaseModel):
    path: str
    max_chars: int = Field(
        default=20_000,
        ge=100,
        le=100_000
    )

class ReadFileTool(RuntimeTool[ReadFileArgs]):
    name = "read_file"
    description = (
        "Read a UTF-8 text file from the repository. "
        "Use for source code, configuration, and documentation."
    )
    effect = ToolEffect.READ_ONLY
    args_model=ReadFileArgs
    
    def __init__(self, workspace: RepositoryWorkspace) -> None:
        self._workspace = workspace
    
    async def execute(self, args: ReadFileArgs):
        path = self._workspace.resolve(args.path)
        
        if not path.exists():
            raise ToolExecutionError(
                code="PATH_NOT_FOUND",
                message=f"File not found: {args.path}"
            )
        
        if not path.is_file():
            raise ToolExecutionError(
                code="NOT_A_FILE",
                message=f"Not a file: {args.path}"
            )
        
        try:
            with path.open('r', encoding="utf-8", errors="replace") as file:
                content = file.read(args.max_chars + 1)
        except OSError as exc:
            raise ToolExecutionError(
                code="FILE_READ_ERROR",
                message=str(exc)
            ) from exc
        
        truncated = len(content) > args.max_chars
        
        if truncated:
            content = content[:args.max_chars]
        
        return {
            "path": args.path,
            "content": content,
            "truncated": truncated,
            "chars_returned": len(content)
        }
    
class ReadFileRangeArgs(BaseModel):
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    
    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        
        line_count = self.end_line - self.start_line + 1
        
        if line_count > 400:
            raise ValueError("A single range may not exceed 400 lines.")
        
        return self

class ReadFileRangeTool(RuntimeTool[ReadFileRangeArgs]):
    name = "read_file_range"
    description = (
        "Read a bounded range of lines from a repository of text file."
        "Prefer this when a large file's relevant section is already known."
    )
    effect = ToolEffect.READ_ONLY
    args_model = ReadFileRangeArgs
    
    def __init__(self, workspace: RepositoryWorkspace) -> None:
        self._workspace = workspace
    
    async def execute(self, args: ReadFileRangeArgs):
        path = self._workspace.resolve(args.path)
        
        if not path.exists():
            raise ToolExecutionError(
                code="PATH_NOT_FOUND",
                message=f"File not found: {args.path}"
            )
        
        if not path.is_file():
            raise ToolExecutionError(
                code="NOT_A_FILE",
                message=f"Not a file: {args.path}"
            )
        
        selected_lines = []
        
        try:
            with path.open('f', encoding="utf-8", errors="replace") as file:
                for line_number, line in enumerate(file, start=1):
                    if line_number < args.start_line:
                        continue
                    if line_number > args.end_line:
                        break
                    
                    selected_lines.append({
                        "line_number": line_number,
                        "text": line.rstrip('\n')
                    })
        except OSError as exc:
            raise ToolExecutionError(
                code="FILE_READ_ERROR",
                message=str(exc)
            ) from exc
        
        return {
            "path": args.path,
            "start_line": args.start_line,
            "end_line": selected_lines[-1]["line_number"] if selected_lines else args.start_line - 1,
            "lines": selected_lines
        }
        