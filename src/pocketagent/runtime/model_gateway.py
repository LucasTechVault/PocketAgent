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

import json
from time import perf_counter
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4

import httpx

from pocketagent.runtime.contracts.common import Message, MessageRole
from pocketagent.runtime.contracts.model import (
    ModelFinishReason,
    ModelRequest, ModelResponse,
    ModelUsage,
    TextOutput
)
from pocketagent.runtime.contracts.tools import (
 ToolDefinition, ToolCallProposal
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

class VLLMModelGateway:
    """ModelGateway implementation for vLLM's OpenAI-compatible API.
    
    Responsibilities:
    1. Translate PocketAgent ModelRequest -> vLLM request payload.
    2. Perform HTTP request.
    3. Translate vLLM response -> PocketAgent ModelResponse.
    """
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 120.0
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=timeout_seconds
        )
    
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Execute one inference request through vLLM."""
        
        payload = self._build_payload(request)
        
        started = perf_counter()
        
        try:
            response = await self._client.post(
                "/chat/completions",
                json=payload
            )
            
            response.raise_for_status()
        
        except httpx.HTTPError as exc:
            raise ModelGatewayError(f"vLLM request failed: {exc}") from exc
        
        latency_ms = int((perf_counter() - started) * 1000)
        
        try:
            raw = response.json()
        except ValueError as exc:
            raise ModelGatewayError("vLLM returned invalid JSON.") from exc
        
        return self._normalize_response(
            request=request,
            raw=raw,
            latency_ms=latency_ms
        )
    
    # Outbound Translation (ModelRequest -> Payload)
    def _build_payload(self, request: ModelRequest) -> dict[str, Any]:
        """Translate PocketAgent ModelRequest into vLLM payload."""
        
        payload: dict[str, Any] = {
            "model": request.model_id,
            "messages": [self._message_to_payload(msg) for msg in request.messages]
        }
        
        if request.max_output_tokens is not None:
            payload["max_tokens"] = request.max_output_tokens
        
        if request.tools:
            payload["tools"] = [self._tool_to_payload(t) for t in request.tools]
        
        return payload
    
    # Inbound Translation (vLLM response -> ModelResponse)
    def _normalize_response(
        self,
        *,
        request: ModelRequest,
        raw: dict[str, Any],
        latency_ms: int
    ) -> ModelResponse:
        """Convert vLLM response into PocketAgent ModelResponse."""
        
        # 1. Normalize model response
        choices = raw.get("choices")
        
        if not isinstance(choices, list) or not choices:
            raise ModelGatewayError("vLLM response contains no choices.")
    
        choice = choices[0]
        
        if not isinstance(choice, dict):
            raise ModelGatewayError("Malformed vLLM Choice.")
    
        msg = choice.get("message")
        
        if not isinstance(msg, dict):
            raise ModelGatewayError("vLLM response contains no message.")
        
        output_items: list[TextOutput | ToolCallProposal] = []
        content = msg.get("content")
        
        if isinstance(content, str) and content:
            output_items.append(TextOutput(text=content))
        
        # 2. Normalize tool calls
        raw_tool_calls = msg.get("tool_calls") or []
        
        if not isinstance(raw_tool_calls, list):
            raise ModelGatewayError("vLLM tool_calls must be a list.")
    
        for rtc in raw_tool_calls:
            output_items.append(self._normalize_tool_call(rtc))
        
        # 3. Normalize usage
        raw_usage = raw.get("usage") or {}
        if not isinstance(raw_usage, dict):
            raw_usage = {}
        
        usage = ModelUsage(
            input_tokens=int(raw_usage.get("prompt_tokens", 0)),
            output_tokens=int(raw_usage.get("completion_tokens", 0))
        )
        
        # 4. Complete Normalization
        provider_id = str(raw.get("id")) or f"vllm-{uuid4()}"
        
        return ModelResponse(
            response_id=provider_id,
            request_id=request.request_id,
            model_id=str(raw.get("model") or request.model_id),
            output_items=output_items,
            finish_reason=self._map_finish_reason(choice.get("finish_reason")),
            usage=usage,
            latency_ms=latency_ms,
            provider_request_id=provider_id,
            metadata={
                "provider": "vllm"
            }
        )


    # Convert PocketAgent messages
    @staticmethod
    def _message_to_payload(msg: Message) -> dict[str, Any]:
        """Translate a PocketAgent Message."""
        
        if msg.role is MessageRole.TOOL:
            raise ModelGatewayError("Tool-result messages are not supported in M02.")

        return {
            "role": msg.role.value,
            "content": msg.content
        }

    # Translate Tool Schemas
    @staticmethod
    def _tool_to_payload(tool: ToolDefinition) -> dict[str, Any]:
        """Translate PocketAgent tool schema.
        
        Exposure to model does not imply permission to execute.
        """

        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
        }
        
    # Used in normalization step
    @staticmethod
    def _normalize_tool_call(raw_tool_call: Any) -> ToolCallProposal:
        """Translate provider toolcall into PocketAgent contract."""
        if not isinstance(raw_tool_call, dict):
            raise ModelGatewayError("Malformed tool call.")

        fn = raw_tool_call.get("function")
        if not isinstance(fn, dict):
            raise ModelGatewayError("Tool call has no function.")
        
        raw_args = fn.get("arguments", '{}')
        if not isinstance(raw_args, str):
            raise ModelGatewayError("Tool arguments must be JSON string.")
        
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError as exc:
            raise ModelGatewayError("Model produced invalid tool args") from exc
        
        if not isinstance(args, dict):
            raise ModelGatewayError("Tool arguments must decode to an object.")
        
        return ToolCallProposal(
            call_id=str(raw_tool_call.get("id") or f"call-{uuid4()}"),
            tool_name=str(fn.get("name")),
            arguments=args
        )
    
    @staticmethod
    def _map_finish_reason(finish_reason: Any) -> ModelFinishReason:
        """Translate provider finish reason."""
        match finish_reason:
            case "stop": return ModelFinishReason.STOP
            case "tool_calls": return ModelFinishReason.TOOL_CALLS
            case "length": return ModelFinishReason.LENGTH
            case _: return ModelFinishReason.OTHER
    
    async def aclose(self) -> None:
        """Release HTTP resources."""

        await self._client.aclose()

    async def __aenter__(
        self,
    ) -> "VLLMModelGateway":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        await self.aclose()
        