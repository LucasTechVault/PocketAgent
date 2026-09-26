from __future__ import annotations

from pocketagent.runtime.tools.gate.base import GateDecision
from pocketagent.runtime.tools.base import RuntimeTool, ToolEffect
from pocketagent.runtime.contracts.tools import ToolCallProposal

class ReadOnlyActionGate:
    """M03 policy - permit only READ_ONLY tools."""
    
    def evaluate(
        self,
        *,
        tool: RuntimeTool,
        proposal: ToolCallProposal
    ) -> GateDecision:
        if tool.effect is not ToolEffect.READ_ONLY:
            return GateDecision(
                allowed=False,
                reason=f"Tool `{proposal.tool_name}` is not READ_ONLY."
            )
        
        return GateDecision(
            allowed=True,
            reason="Read-only capability permitted."
        )