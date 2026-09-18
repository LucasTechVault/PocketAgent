"""Common runtime primitives.

These types are intentionally application-neutral.

They remain neutral whether PocketAgent is Coding Agent, Research Agent, Document Workbench, Browser Agent, or future Computer-Integrated Assistant.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, JsonValue, StringConstraints

from pocketagent.runtime.contracts.base import ContractModel

# Custom Field Type for Validation
NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1)
    ]

class RunStatus(StrEnum):
    """Lifecycle state of a PocketAgent run.
    
    M01:
        Defines vocab only.
    
    M06:
        Termination / control logic will decide when transitions between these statuses are legal.
    """
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class MessageRole(StrEnum):
    """Provider-neutral message roles used by runtime."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(ContractModel):
    """One message known to runtime.
    
    M02/M04 will decide which messages are sent to model.
    """
    
    message_id: NonEmptyStr
    role: MessageRole
    content: str
    
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

class ArtifactRef(ContractModel):
    """Reference to potentially large external artifact.
    
    RuntimeState stores reference rather than forcing entire artifact into every state snapshot.
    """
    
    artifact_id: NonEmptyStr
    uri: NonEmptyStr
    media_type: NonEmptyStr
    
    size_bytes: int | None = Field(default=None, ge=0) # greater or equal to 0
    
    # JsonValue = any value legally serializable to JSON
    # default_factory=dict -> create new dict on every new instance
    metadata: dict[str, JsonValue] = Field(default_factory=dict) 