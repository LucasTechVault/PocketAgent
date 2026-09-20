"""PocketAgent Agent Runtime primitives."""

from pocketagent.runtime.patch import RuntimeStatePatch
from pocketagent.runtime.reducer import (
    StateReductionError,
    reduce_state,
)
from pocketagent.runtime.state import RuntimeState

__all__ = [
    "RuntimeState",
    "RuntimeStatePatch",
    "StateReductionError",
    "reduce_state",
]