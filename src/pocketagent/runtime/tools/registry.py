"""Authoritative registry of PocketAgent capabilites.

Menu of Tools to select from - What tools exist?
"""

from __future__ import annotations

from typing import Any

from pocketagent.runtime.contracts.tools import ToolDefinition
from pocketagent.runtime.tools.base import RuntimeTool

class ToolRegistryError(RuntimeError):
    """Raised for invalid registry configuration."""

class ToolRegistry:
    """Stores executable capabilities by exact tool name."""
    
    def __init__(self) -> None:
        self._tools: dict[str, RuntimeTool[Any]] = {}
    
    def register(self, tool: RuntimeTool[Any]) -> None:
        """Register one tool."""
        if tool.name in self._tools:
            raise ToolRegistryError("Tool already registered: {tool.name}")
        
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> RuntimeTool[Any] | None:
        """Return exact registered capability."""
        return self._tools.get(name)

    def definitions(self) -> list[ToolDefinition]:
        """Return schemas exposed to model."""
        
        return [tool.definition for tool in self._tools.values()]