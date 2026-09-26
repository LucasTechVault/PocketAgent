"""Canonical PocketAgent Runtime State."""

from typing import Self

from pydantic import Field, JsonValue, model_validator

from pocketagent.runtime.contracts.base import ContractModel
from pocketagent.runtime.contracts.budget import BudgetState # Wrapper holding BudgetLimit & BudgetUsage
from pocketagent.runtime.contracts.common import (
    ArtifactRef,
    Message,
    NonEmptyStr,
    RunStatus
)
from pocketagent.runtime.contracts.termination import TerminationState
from pocketagent.runtime.contracts.tools import ToolCallRecord # Wrapper holding ToolCall-related contracts
from pocketagent.runtime.contracts.trace import TraceContext # For tracing

class RuntimeState(ContractModel):
    """Canonical mutable facts for one PocketAgent execution run."""
    
    state_version: int = Field(default=1, ge=1) # schema version for tracking updates
    # if fields updated, version changes, helps keep track of any pydantic issues.
    
    run_id: NonEmptyStr # uuid for run
    
    session_id: NonEmptyStr | None = None # optional id for multiple related runs link
    
    step: int = Field(default=0, ge=0) # Num runtime steps - for budget tracking / checkpointing
    
    status: RunStatus = RunStatus.RUNNING
    
    current_node: NonEmptyStr # Placeholder for current runtime location.
    
    messages: list[Message] = Field(default_factory=list) # Full runtime interaction history.
    
    tool_calls: list[ToolCallRecord] = Field(default_factory=list) # Structured history of proposed / execution tool activity.
    
    artifacts: dict[str, ArtifactRef] = Field(default_factory=dict) # References to external / large artifacts
    
    # Behavior / Application State ==================================================
    # (Phase A - 19 Sep 2026 22:59)
    # 
    # Phase B -> TaskBeliefState 
    # Phase C -> Coding / Research-specific state
    working_memory: dict[str, JsonValue] = Field(default_factory=dict)
    
    # ================================================================================
    
    budget: BudgetState # Runtime-owned resource accounting
    
    termination: TerminationState = Field(default_factory=TerminationState) # M06 update this via TerminationPolicy
    
    trace: TraceContext # Correlation identity for tracing
    
    @model_validator(mode="after")
    def validate_artifact_index(self) -> Self:
        """Artifact dict keys must agree with ArtifactRef IDs."""
        
        for key, artifact in self.artifacts.items():
            if key != artifact.artifact_id:
                raise ValueError("Artifact dictionary key must match artifact_id: "
                                 f"{key!r} != {artifact.artifact_id!r}")
        
        return self
    