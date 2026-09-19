"""Runtime resource-budget contracts.

    Agent runtime uses reasoning loop.
    Loop must be bounded.
    
    M01 -> Stores limit & usage facts.
    M02 -> Control loop begins updating usage
    M06 -> Termination policy interprets values & decides
    
    BudgetState -> Stores facts
    TerminationPolicy -> Applies policy
"""

from pydantic import Field

from pocketagent.runtime.contracts.base import ContractModel

class BudgetLimits(ContractModel):
    """Configured upper bounds for 1 runtime run.
    
    None -> specific dimension not configured yet.
    
    M06 -> Enforce production runs have appropriate hard limtis.
    """
    
    max_turns: int | None = Field(default=None, gt=0)
    max_tool_calls: int | None = Field(default=None, gt=0)
    max_wall_ms: int | None = Field(default=None, gt=0) # loop running time
    max_input_tokens: int | None = Field(default=None, gt=0)
    max_output_tokens: int | None = Field(default=None, gt=0)
    max_cost_usd: float | None = Field(default=None, ge=0) # if using hosted models

class BudgetUsage(ContractModel):
    """Resources consumed so far by the run."""
    
    turns_used: int = Field(default=0, ge=0)
    tool_calls_used: int = Field(default=0, ge=0)
    wall_ms_used: int = Field(default=0, ge=0)
    input_tokens_used: int = Field(default=0, ge=0)
    output_tokens_used: int = Field(default=0, ge=0)
    cost_usd_used: float = Field(default=0.0, ge=0) # if using hosted models

class BudgetState(ContractModel):
    """Wrapper for BudgetLimit + BudgetUsage"""
    limits: BudgetLimits
    usage: BudgetUsage = Field(default_factory=BudgetUsage)