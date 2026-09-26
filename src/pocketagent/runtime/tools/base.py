"""Core executable tool abstraction for PocketAgent.

M01 - Defined Tool-related DATA contracts.
M03 - Introduces actual executable capabilties.

RuntimeTool binds:

    model-visible ToolDefinition
        +
    deterministic implementation
        +
    side-effect classification (Modifies something)

Model sees only ToolDefinition.
Runtime owns execute()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, JsonValue

from pocketagent.runtime.contracts.tools import ToolDefinition

# Can be any class, so long as inherit from BaseModel
ArgsT = TypeVar("ArgsT", bound=BaseModel)

class ToolEffect(StrEnum):
    """Broad capability class used by ActionGate."""
    
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"
    EXECUTION = "EXECUTION"

class ToolExecutionError(RuntimeError):
    """Expected deterministic failure during tool execution.
    
    i.e. Network error / Rate Limit / External service error etc.
    Need to normalize for decision making instead of throwing error
    """
    
    def __init__(
        self,
        *,
        code: str,
        message: str,
        retryable: bool = False, # Unauthorized / Invalid API key should not be retried
        details: dict[str, JsonValue] | None = None
    ) -> None:
        super().__init__(message)
        
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}

class RuntimeTool(ABC, Generic[ArgsT]):
    """Executable capability owned by PocketAgent runtime."""
    
    # Sources of truth
    name: str
    description: str
    effect: ToolEffect
    args_model: type[ArgsT]
    
    # Derived from sources of truth
    @property
    def definition(self) -> ToolDefinition:
        """Create the model-visible schema."""
        
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.args_model.model_json_schema()
        )
    
    @abstractmethod
    async def execute(self, args: ArgsT) -> JsonValue:
        """Execute validated deterministic behavior."""