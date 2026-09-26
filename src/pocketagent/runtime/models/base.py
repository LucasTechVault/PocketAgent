"""Model inference boundary for PocketAgent.

M02 responsibility 20 Sep 2026 12:08

(Anti Corruption Layer)
Gateway between internal Runtime and external Model Serving Engine
- Map internal RuntimeState to ModelRequest for external usage
- Parse external response to ModelResponse for internal Runtime usage.

ControlLoop depends only on ModelGateway.

It must NOT know:
    - HTTP payload formats
    - vLLM response structure
    - OpenAI-compatible field names
    - Provider-specific finish reasons

Future Implementation:
    - VLLMModelGateway
    - SGLangModeGateway
    - hosted-provider adapters

1. HostedHttpGateway (HTTP to cloud providers)
    - AnthropicHttpAdapter
    - OpenAIHttpAdapter

2. VLLMProcessGateway
    - Llama3ChatTemplateAdapter (Llama3 model)
    - QwenGuidedDecodingAdapter (Qwen model)

"""

from __future__ import annotations

from time import perf_counter
from typing import Protocol, runtime_checkable

from pocketagent.runtime.contracts.common import MessageRole
from pocketagent.runtime.contracts.model import (
    ModelRequest, ModelResponse
)

class ModelGatewayError(RuntimeError):
    """Raised when inference boundary cannot produce a valid response."""

@runtime_checkable
class ModelGateway(Protocol):
    """Provider neutral inference interface used by PocketAgent runtime.
    
    The runtime only knows this contract.
    
    Implementation may communicate with:
    - Local vLLM
    - remote vLLM
    - SGLang
    - Hosted APIs
    
    without requiring ControlLoop to change.
    """
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Execute one model inference request."""
        ...
