"""Execution of one PocketAgent runtime step.

(M02 responsibility 26 Sep 2026 09:21)
Move PocketAgent from RuntimeState N to RuntimeState N+1 exactly once.

One model-driven step performs:

RuntimeState N
|
PromptRenderer (Strategy Pattern)
|
ModelRequest
|
ModelGateway (Adapter Pattern)
|
ModelResponse
|
interpret response
|
RuntimeStatePatch
|
reducer 
|
RuntimeState N+1

This module does not decide whether another step may execute.
That responsibility belongs to the ControlLoop.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from pocketagent.runtime.contracts.budget import (
    BudgetState,
    BudgetUsage
)

from pocketagent.runtime.contracts.common import (
    Message, MessageRole,
    RunStatus
)

from pocketagent.runtime.contracts.model import (
    ModelFinishReason,
    ModelRequest, ModelResponse,
    TextOutput
)

from pocketagent.runtime.contracts.termination import TerminationState

from pocketagent.runtime.contracts.tools import (
    ToolCallProposal, ToolCallRecord
)

from pocketagent.runtime.models.base import (
    ModelGateway,
    ModelGatewayError
)

from pocketagent.runtime.state.patch import RuntimeStatePatch
from pocketagent.runtime.prompts.base import PromptRenderer
from pocketagent.runtime.state.reducer import reduce_state
from pocketagent.runtime.state.state import RuntimeState

@dataclass(frozen=True, slots=True)
class RuntimeStepResult:
    """Complete observable result of one runtime step.
    
    This is deliberately NOT RuntimeState.
    It is just an internal execution envelope for observation.
    
    It represents what happened while producing the next state and will
    later be useful for tracing, eval, and persistence.
    """
    
    request: ModelRequest
    response: ModelResponse | None
    patch: RuntimeStatePatch
    next_state: RuntimeState

class RuntimeStep:
    """Executes exactly one model-driven runtime transition."""
    
    def __init__(
        self,
        *,
        model_gateway: ModelGateway, # Receives the interface to keep generic (dependency inversion)
        prompt_renderer: PromptRenderer,
        model_id: str,
        max_output_tokens: int = 1024
    ) -> None:
        if not model_id.strip():
            raise ValueError("model_id must not be empty.")
        
        if max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be greater than zero.")
    
        self._model_gateway = model_gateway
        self._prompt_renderer = prompt_renderer
        self._model_id = model_id
        self._max_output_tokens = max_output_tokens
        
    async def execute(
        self,
        state: RuntimeState
    ) -> RuntimeStepResult:
        """Executes exactly one runtime step."""
        if state.status is not RunStatus.RUNNING:
            raise ValueError("RuntimeStep requires a RUNNING RuntimeState.")
    
        rendered_messages = self._prompt_renderer.render(state)
        
        request = ModelRequest(
            request_id=f"request-{uuid4()}",
            model_id=self._model_id,
            messages=rendered_messages,
            tools=[], # M03 introduces tools 26 Sep 2026 12:04
            max_output_tokens = self._max_output_tokens,
            metadata={
                "run_id": state.run_id,
                "step": state.step,
                "trace_id": state.trace.trace_id
            }
        )   
        
        started = perf_counter()
        
        try:
            res = await self._model_gateway.generate(request)
        except ModelGatewayError as exc:
            elapsed_ms = int((perf_counter() - started) * 1000)
            
            error_patch = self._gateway_error_patch(
                state=state,
                elapsed_ms=elapsed_ms,
                error=exc
            )
            
            next_state = reduce_state(state, error_patch)
            
            return RuntimeStepResult(
                request=request,
                response=None,
                patch=error_patch,
                next_state=next_state
            )
        
        patch = self._response_to_patch(
            state=state,
            response=res
        )
        
        next_state = reduce_state(state, patch)
        
        return RuntimeStepResult(
            request=request,
            response=res,
            patch=patch,
            next_state=next_state
        )
    
    # Handling response (render response)
    def _response_to_patch(
        self,
        *,
        state: RuntimeState,
        response: ModelResponse
    ) -> RuntimeStatePatch:
        """Translate model output into explicit state update."""
        
        # 1.1 Text proposed by model (ASSISTANT)
        text_outputs = [
            item
            for item in response.output_items
            if isinstance(item, TextOutput)
        ]
        
        # 1.2 Actions proposed by model
        tool_proposals = [
            item
            for item in response.output_items
            if isinstance(item, ToolCallProposal)
        ]
        
        # 2. Convert text to runtime message
        messages_append: list[Message] = []
        
        # 2.1 Handle ASSISTANT output
        combined_text = '\n'.join(
            output.text
            for output in text_outputs
        ).strip()
        
        if combined_text:
            messages_append.append(
                Message(
                    message_id=f"model:{response.response_id}",
                    role=MessageRole.ASSISTANT,
                    content=combined_text,
                    metadata={
                        "model_id": response.model_id,
                        "response_id": response.response_id
                    }
                )
            )
        
        # 2.2 Handle Tool Proposals 
        tool_records = [ToolCallRecord(proposal=proposal) for proposal in tool_proposals] 
        
        # 3. Update budget usage
        next_budget = self._budget_after_response(state=state, response=response)
        
        # 4. HandleSemantic completion criterion
        # Keep it simple for M02 26 Sep 2026 12:34
        if (
            response.finish_reason is ModelFinishReason.STOP
            and combined_text
            and not tool_proposals
        ):
            return RuntimeStatePatch(
                step=state.step + 1,
                messages_append=messages_append,
                budget=next_budget,
                status=RunStatus.COMPLETED,
                termination=TerminationState(
                    requested=True,
                    reason_code="MODEL_FINAL_OUTPUT",
                    detail="Model produced final textual response."
                )
            
            )
        
        # 5. Handle ToolCallProposal
        if tool_proposals:
            return RuntimeStatePatch(
                step=state.step + 1,
                messages_append=messages_append,
                tool_calls_append=tool_records,
                budget=next_budget,
                status=RunStatus.FAILED,
                termination=TerminationState(
                    requested=True,
                    reason_code="M02_TOOLCALL_UNSUPPORTED",
                    detail=(
                        "The model proposed a tool call,"
                        "but tool execution begins in M03."
                    )
                )
            )
        
        # 6. Handle remaining model output scenario
        if response.finish_reason is ModelFinishReason.ERROR:
            reason_code = "MODEL_RESPONSE_ERROR"
        
        elif response.finish_reason is ModelFinishReason.LENGTH:
            reason_code = "MODEL_OUTPUT_TRUNCATED"
            
        elif response.finish_reason is ModelFinishReason.INCOMPLETE:
            reason_code = "MODEL_RESPONSE_INCOMPLETE"
        
        elif not combined_text:
            reason_code = "EMPTY_MODEL_RESPONSE"
        
        else:
            reason_code = "UNSUPPORTED_MODEL_FINISH_REASON"
        
        return RuntimeStatePatch(
            step=state.step + 1,
            messages_append=messages_append,
            tool_calls_append=tool_records,
            budget=next_budget,
            status=RunStatus.FAILED,
            termination=TerminationState(
                requested=True,
                reason_code=reason_code,
                detail=(
                    "Model response could not be interpreted."
                    f"finish_reason={response.finish_reason.value}"
                )
            )
        )

    @staticmethod
    def _budget_after_response(
        *,
        state: RuntimeState,
        response: ModelResponse
    ) -> BudgetState:
        """Account for resources consumed by one model invocation."""
        
        previous_usage = state.budget.usage
        next_usage = BudgetUsage(
            turns_used= previous_usage.turns_used + 1,
            tool_calls_used=previous_usage.tool_calls_used,
            wall_ms_used=previous_usage.wall_ms_used + response.latency_ms,
            input_tokens_used=previous_usage.input_tokens_used + response.usage.input_tokens,
            output_tokens_used=previous_usage.output_tokens_used + response.usage.output_tokens,
            cost_usd_used=previous_usage.cost_usd_used
        )
        
        return BudgetState(
            limits=state.budget.limits,
            usage=next_usage
        )
        
    @staticmethod
    def _gateway_error_patch(
        *,
        state: RuntimeState,
        elapsed_ms: int,
        error: ModelGatewayError
    ) -> RuntimeStatePatch:
        """Convert an interface-boundary failure into terminal state."""
        
        previous = state.budget.usage
        
        next_usage = BudgetUsage(
            turns_used=previous.turns_used + 1,
            tool_calls_used=previous.tool_calls_used,
            wall_ms_used=previous.wall_ms_used + elapsed_ms,
            input_tokens_used=previous.input_tokens_used,
            output_tokens_used=previous.output_tokens_used,
            cost_usd_used=previous.cost_usd_used
        )
        
        next_budget = BudgetState(
            limits=state.budget.limits,
            usage=next_usage
        )
        
        return RuntimeStatePatch(
            step=state.step + 1,
            budget=next_budget,
            status=RunStatus.FAILED,
            termination=TerminationState(
                requested=True,
                reason_code="MODEL_GATEWAY_ERROR",
                detail=str(error)
            )
        )