"""Deterministic RuntimeState reducer.

Reducer is the sole judge, jury and executor of state update.
In naive software design, individual workers decide how data changes.
    - if worker mess up & overrides Message = System breaks
    
Different fields = different semantics = different update rule

Linear Timeline:
    messages & tool_calls -> Append 

Shared: (heavy)
    artifacts -> Upsert / Remove by key

Shared (shallow + top-level)
    - shallow -> only merge top-level keys (don't deep recurse)
    working_memory -> Top-level Upsert / Remove

Scalars (single value)
    step, status, current_node, budget -> replace
"""

from pocketagent.runtime.patch import RuntimeStatePatch
from pocketagent.runtime.state import RuntimeState

class StateReductionError(RuntimeError):
    """Raised when a patch violates reducer-level state invariants."""
    
def reduce_state(
    state: RuntimeState,
    patch: RuntimeStatePatch
    ) -> RuntimeState:
    """Apply a RuntimeStatePatch and return a NEW validated RuntimeState.
    
    Note:
        The input RuntimeState is not mutated.
        
        M01: 20 Sep 2026 08:49
            Intentional SHALLOW working_memory patching
            Phase B defines TaskBeliefState reducer (arbitrary recursive dict merge)
    """
    
    new_state = state.model_dump(mode="python") # create a copy

    # =====================================================================================
    #  APPEND semantics (Linear Timeline components)
    new_state["messages"] = [*state.messages, *patch.messages_apend]
    new_state["tool_calls"] = [*state.tool_calls, *patch.tool_calls_append]
    
    # =====================================================================================
    # UPSERT / REMOVE semantics (Heavy)
    new_artifacts = dict(state.artifacts)
    
    for artifact_id in patch.artifacts_remove:
        new_artifacts.pop(artifact_id, None)
    
    new_artifacts.update(patch.artifacts_upsert)
    new_state["artifacts"] = new_artifacts
    
    # =====================================================================================
    # UPSERT / REMOVE semantics (Shallow)
    new_working_memory = dict(state.working_memory)
    
    for key in patch.working_memory_remove:
        new_working_memory.pop(key, None)
    
    new_working_memory.update(patch.working_memory_upsert)
    new_state["working_memory"] = new_working_memory
    
    # =====================================================================================
    # SCALARs - Replace
    if patch.step is not None:
        if patch.step < state.step:
            raise StateReductionError("RuntimeState.step cannot move backwards.")
    
        new_state["step"] = patch.step
    
    if patch.current_node is not None:
        new_state["current_node"] = patch.current_node
        
    if patch.status is not None:
        new_state["status"] = patch.status
    
    if patch.budget is not None:
        new_state["budget"] = patch.budget
    
    # RuntimeState validation
    reduced = RuntimeState.model_validate(new_state)
    
    if reduced.run_id != state.run_id:
        raise StateReductionError("Reducer must not change run_id.")

    if reduced.session_id != state.session_id:
        raise StateReductionError("Reducer must not change session_id.")
    
    if reduced.state_version != state.state_version:
        raise StateReductionError("Reducer must not change state_version.")

    return reduced

    """ID Hierarchy
    
    Session ID (Chat Window / Thread)
        Run ID (1 user prompt -> execution until final answer)
            Trace ID (Observability / Trace logs)
                Span ID (1 specific step: tool call, LLM request)
    """
      