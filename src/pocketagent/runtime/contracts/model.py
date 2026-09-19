"""Provider-neutral model

    M01:
        Defines ModelRequest & ModelResponse
    
    M02:
        ModelGateway consumes ModelRequest & return ModelResponse
    
    M12:
        Different inference adapters can map these contracts to hosted APIs.
        (local models / remote models)
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, JsonValue

from pocketagent.runtime.contracts.base import ContractModel
from pocketagent.runtime.contracts.common import (
    Message, # Force external models to speak PocketAgent internal Message model.
    NonEmptyStr
)
from pocketagent.runtime.contracts.tools import (
    ToolCallProposal, # Returned by model
    ToolDefinition # Pass to model
)

class ModelUsage(ContractModel):
    """Resource usage reported for 1 model invocation."""
    input_tokens: int = Field(default=0, ge=0) 
    output_tokens: int = Field(default=0, ge=0)

class ModelFinishReason(StrEnum):
    """Provider-neutral reason the model invocation ended."""
    
    STOP = "STOP"
    TOOL_CALLS = "TOOL_CALLS"
    LENGTH = "LENGTH"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"
    OTHER = "OTHER"

class TextOutput(ContractModel):
    """Textual output produced by model."""
    
    kind: Literal["text"] = "text"
    text: str
    
ModelOutputItem = Annotated[
    TextOutput | ToolCallProposal, # output can be either
    Field(discriminator="kind") # use field `kind` to instantiate 
    # TextOutput & ToolCallProposal need `kind` as field
]

class ModelRequest(ContractModel):
    """Request sent from PocketAgent Runtime to model backend.
    
    M02 ModelGateway consumes this contract.
    
    ToolDefinition describe capabilities visible to model.
    They do not imply authorization to execute.
    """
    
    request_id: NonEmptyStr # request uuid
    
    model_id: NonEmptyStr # "gpt-4o" / "claude-3-5-sonnet" (for model routing)
    
    messages: list[Message] = Field(default_factory=list) # point to new list
    
    tools: list[ToolDefinition] = Field(default_factory=list) # capabilities
    
    max_output_tokens: int | None = Field(default=None, gt=0)
    
    metadata: dict[str, JsonValue] = Field(default_factory=dict) # extensible catch-all for key-value pairs not specified in message / tools

class ModelResponse(ContractModel):
    """Normalized response returned by ModelGateway
    
    Model Serving Engine -> ModelGateway (validation + normalize) -> Agent Runtime
    
    Agent Runtime consumes this form rather than provider-specific wire responses.
    """
    
    # Generated internally by System.
    response_id: NonEmptyStr # 1 Request may have many Response (due Retry)
    request_id: NonEmptyStr # To map request to response (1-to-1 r/s)
    
    model_id: NonEmptyStr # the exact version of model that produced this
    
    output_items: list[ModelOutputItem] = Field(default_factory=list) # 1 Response can have multiple due to reasoning
    
    finish_reason: ModelFinishReason
    
    usage: ModelUsage = Field(default_factory=ModelUsage) 
    
    latency_ms: int = Field(default=0, ge=0)
    
    provider_request_id: NonEmptyStr | None = None # model-provider id - created by upstream 3rd party provider.
    
    metadata: dict[str, JsonValue] = Field(default_factory=dict)