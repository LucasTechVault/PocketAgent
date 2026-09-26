"""Minimal PocketAgent lifecycle supervisor.

M02 responsibility:
    Repeatedly execute RuntimeStep while run remains eligble to continue.

ControlLoop owns:
    - guard
    - execution of 1 RuntimeStep
    - Inspect new RuntimeState
    - repeat / stop

M02 adds 1 infra guard - max_turns
M05 adds checkpoint / pause / resume boundaries
M06 introduces full termination policy, cancellation, deadlines, token/cost budgets & topology.
"""

from __future__ import annotations

from pocketagent.runtime.contracts.common import RunStatus
from pocketagent.runtime.contracts.termination import TerminationState

from pocketagent.runtime.state.patch import RuntimeStatePatch
from pocketagent.runtime.state.reducer import reduce_state
from pocketagent.runtime.state.state import RuntimeState
from pocketagent.runtime.step import RuntimeStep

class ControlLoopConfigurationError(RuntimeError):
    """Raised when required M02 runtime limits are missing."""

class ControlLoop:
    """Minimal lifecycle supervisor for PocketAgent.
    
    Loop only knows RuntimeStep.
    Unaware of ModelGateway / PromptRenderer
    """
    
    def __init__(self, *, runtime_step: RuntimeStep) -> None:
        self._runtime_step = runtime_step
    
    async def run(self, initial_state: RuntimeState) -> RuntimeState:
        """Execute steps until run reaches terminal state.
        
        Passing initial_state makes control loop stateless & resuable.
        On step 0, initial_state = initial user request + empty history.
        """
        
        state = initial_state
        
        while state.status is RunStatus.RUNNING:
            
            # CHECK THEN EXECUTE
            if self._hard_turn_limit_reached(state):
                state = self._terminate_for_turn_limit(state)
                break
                
            step_result = await self._runtime_step.execute(state)
            state = step_result.next_state
        
        return state

    @staticmethod
    def _hard_turn_limit_reached(state: RuntimeState) -> bool:
        """Check whether another model invocation is permitted."""
        
        max_turns = state.budget.limits.max_turns
        
        if max_turns is None:
            raise ControlLoopConfigurationError("M02 requires BudgetLimits.max_turns.")
        
        return state.budget.usage.turns_used >= max_turns

    @staticmethod
    def _terminate_for_turn_limit(state: RuntimeState) -> RuntimeState:
        """Produce terminal state without another model invocation.
        
        Does not directly override state.status = Failed
        Follow RuntimeState + RuntimeStatePatch -> Reducer -> New RuntimeState
        """
        
        termination_patch = RuntimeStatePatch(
            status=RunStatus.FAILED,
            termination=TerminationState(
                requested=True,
                reason_code="MAX_TURNS_EXCEEDED",
                detail=(
                    "Runtime stopped before another "
                    "model invocation because the hard "
                    "turn limit was reached."
                )
            )
        )
        
        return reduce_state(state, termination_patch)