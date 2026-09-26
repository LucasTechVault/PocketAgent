"""Explicit RuntimeState update contract.

Components should not freely mutate arbitrary fields of RuntimeState.

1. Runtime components should propose small state change
2. RuntimeStatePatch performs update via reducer

M02:
    Control Loop begins producing patches.
    
M03:
    Tool execution produces tool-record / artifact patches.
    
M08+:
    behavior-specific reducers may update namespaced working memory.
"""

from typing import Self

from pydantic import Field, JsonValue, model_validator

# Import similar to RuntimeState
from pocketagent.runtime.contracts.base import ContractModel
from pocketagent.runtime.contracts.budget import BudgetState
from pocketagent.runtime.contracts.common import (
    ArtifactRef,
    Message,
    NonEmptyStr,
    RunStatus
)
from pocketagent.runtime.contracts.termination import TerminationState
from pocketagent.runtime.contracts.tools import ToolCallRecord

class RuntimeStatePatch(ContractModel):
    """Explicit changes to apply to one RuntimeState."""
    
    messages_append: list[Message] = Field(default_factory=list)
    tool_calls_append: list[ToolCallRecord] = Field(default_factory=list)
    artifacts_upsert: dict[str, ArtifactRef] = Field(default_factory=dict)
    artifacts_remove: set[NonEmptyStr] = Field(default_factory=set)
    working_memory_upsert: dict[str, JsonValue] = Field(default_factory=dict) # update memory
    working_memory_remove: set[NonEmptyStr] = Field(default_factory=set) # remove obsolete memory
    
    # Scalar replacement semantics - how single primitives are updated
    # None: No updates. value = update to that value
    step: int | None = Field(default=None, ge=0)
    
    # Control Plane & metadata of execution
    # These fields control where the execution is right now / how healthy / if it must stop.
    current_node: NonEmptyStr | None = None
    status: RunStatus | None = None
    budget: BudgetState | None = None
    termination: TerminationState | None = None
    
    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        """Reject ambiguous patch operations."""
        
        artifact_overlap = set(self.artifacts_upsert) & self.artifacts_remove
        if artifact_overlap:
            raise ValueError(f"Artifact cannot be upserted and remove in same patch: {sorted(artifact_overlap)}")
        
        working_memory_overlap = set(self.working_memory_upsert) & self.working_memory_remove
        if working_memory_overlap:
            raise ValueError(f"Working-memory key cannot be upserted and removed in same patch: {sorted(working_memory_overlap)}")
        
        for key, artifact in self.artifacts_upsert.items():
            if key != artifact.artifact_id:
                raise ValueError(f"Artifact upsert key must match artifact_id: {key!r} != {artifact.artifact_id!r}")
        return self
    