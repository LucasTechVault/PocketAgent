"""Tracing / Correlation contracts.

M01:
    Establish stable correlation identity.
    
M07:
    OpenTelemetry to turn IDs into real traces/spans/metrics.
    
These contracts should not depend directly on observability vendor.
"""

from pydantic import Field, JsonValue

from pocketagent.runtime.contracts.base import ContractModel
from pocketagent.runtime.contracts.common import NonEmptyStr

class TraceContext(ContractModel):
    """Correlation identity attached to a runtime trajectory.
    
    Runtime Trajectory -> step-by-step history of what agent did during a run.
    Correlation identity -> trace_id tagged to every piece of data.
        - 50 users may be running agents at the same time.
    """
    
    trace_id: NonEmptyStr # global id for 1 complete user task / run (6 loops + 14 API calls same id)
    
    correlation_id: NonEmptyStr | None = None # id from outside service, for matching
    parent_span_id: NonEmptyStr | None = None # id of immediate parent step that triggered this step.
    
    attributes: dict[str, JsonValue] = Field(default_factory=dict) # extra context dump
    