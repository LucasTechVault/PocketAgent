"""Read-only repository-analysis capability package."""

from pathlib import Path

from pocketagent.runtime.tools.executor import ToolExecutor
from pocketagent.runtime.tools.gate.read_only import ReadOnlyActionGate
from pocketagent.runtime.tools.registry import ToolRegistry
from pocketagent.runtime.tools.runtime import ToolRuntime
from pocketagent.runtime.tools.repository.tools import (
    FindFilesTool,
    ListDirectoryTool,
    ReadFileRangeTool,
    ReadFileTool,
    SearchTextTool,
)
from pocketagent.runtime.tools.repository.workspace import (
    RepositoryWorkspace,
)


def build_read_only_repository_tool_runtime(
    root: str | Path,
) -> ToolRuntime:
    """Build PocketAgent's initial repository-analysis tool runtime."""

    workspace = RepositoryWorkspace(root)

    registry = ToolRegistry()

    registry.register(
        ListDirectoryTool(workspace)
    )

    registry.register(
        ReadFileTool(workspace)
    )

    registry.register(
        ReadFileRangeTool(workspace)
    )

    registry.register(
        SearchTextTool(workspace)
    )

    registry.register(
        FindFilesTool(workspace)
    )

    gate = ReadOnlyActionGate()

    executor = ToolExecutor(
        registry=registry,
        action_gate=gate,
    )

    return ToolRuntime(
        registry=registry,
        executor=executor,
    )


__all__ = [
    "RepositoryWorkspace",
    "build_read_only_repository_tool_runtime",
]