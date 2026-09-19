""" Termination-state contract.

Purpose: To have / track information on why agent loop terminated.

If simply break loop + set STATUS = DONE, no context on reason why.

M01:
    Define termination contract (information representation)

M06:
    TerminationPolicy to evaluate budgets / cancellation / completion / waiting / no-progress
"""

from typing import Self # method returning instance of its own class

from pydantic import model_validator

from pocketagent.runtime.contracts.base import ContractModel
from pocketagent.runtime.contracts.common import NonEmptyStr

class TerminationState(ContractModel):
    """Current termination request/result attached to run."""
    
    requested: bool = False # Use to propagate through runtime for graceful termination.
    
    reason_code: NonEmptyStr | None = None
    detail: str | None = None
    
    @model_validator(mode="after")
    def validate_requested_reason(self) -> Self:
        if self.requested and self.reason_code is None:
            raise ValueError("TerminationState.requested=True requires reason_code.")
    
        return self
