"""Controlled execution pipeline for ToolCallProposal

How does an approved proposal become a deterministic execution result?

proposal
    ↓
registry lookup
    ↓
ActionGate
    ↓
argument validation
    ↓
tool.execute()
    ↓
ToolResult / ToolError
    ↓
ToolCallRecord
"""

from __future__ import annotations

from time import perf_counter

from pydantic import ValidationError

from pocketagent.runtime.contracts.tools import (
    ToolCallProposal,
    ToolCallRecord,
    ToolCallStatus,
    ToolError,
    ToolResult
)

from pocketagent.runtime.tools.base import ToolExecutionError
from pocketagent.runtime.tools.gate.base import ActionGate
from pocketagent.runtime.tools.registry import ToolRegistry

class ToolExecutor:
    """Deterministically process one proposed action."""
    
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        action_gate: ActionGate
    ) -> None:
        self._registry = registry
        self._action_gate = action_gate
    
    async def execute(self, proposal: ToolCallProposal) -> ToolCallRecord:
        
        # 1. Check capability exist.
        tool = self._registry.get(proposal.tool_name)
        
        if tool is None: # Normalize, for model decision-making
            return ToolCallRecord(
                proposal=proposal,
                status=ToolCallStatus.REJECTED,
                error=ToolError(
                    call_id=proposal.call_id,
                    code="TOOL_NOT_FOUND",
                    message=f"Tool is not registered: {proposal.tool_name}"
                )
            )
        
        # 2. Check action allowed.
        decision = self._action_gate.evaluate(
            tool=tool,
            proposal=proposal
        )
        
        if not decision.allowed:
            return ToolCallRecord(
                proposal=proposal,
                status=ToolCallStatus.REJECTED,
                error=ToolError(
                    call_id=proposal.call_id,
                    code="ACTION_DENIED",
                    message=decision.reason,
                    retryable=False
                )
            )
        
        # 3. Check tool-arguments valid?
        try:
            validated_args = tool.args_model.model_validate(proposal.arguments)
        except ValidationError as exc:
            return ToolCallRecord(
                proposal=proposal,
                status=ToolCallStatus.REJECTED,
                error=ToolError(
                    call_id=proposal.call_id,
                    code="ARGUMENT_VALIDATION_ERROR",
                    message=str(exc),
                    retryable=False
                )
            )
        
        # 4. Execute deterministic implementation
        started = perf_counter()
        
        try:
            output = await tool.execute(validated_args)
        except ToolExecutionError as exc:
            latency_ms = int((perf_counter() - started) * 1000)
            
            return ToolCallRecord(
                proposal=proposal,
                status=ToolCallStatus.FAILED,
                error=ToolError(
                    call_id=proposal.call_id,
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                    details=exc.details
                )
            )
        
        except Exception as exc:
            return ToolCallRecord(
                proposal=proposal,
                status=ToolCallStatus.FAILED,
                error=ToolError(
                    call_id=proposal.call_id,
                    code="UNEXPECTED_TOOL_ERROR",
                    message="Tool execution failed unexpectedly.",
                    retryable=False,
                    details={
                        "exception_type": type(exc).__name__
                    }
                )
            )
        
        latency_ms = int((perf_counter() - started) * 1000)
        
        return ToolCallRecord(
            proposal=proposal,
            status=ToolCallStatus.SUCCEEDED,
            result=ToolResult(
                call_id=proposal.call_id,
                output=output,
                latency_ms=latency_ms
            )
        )