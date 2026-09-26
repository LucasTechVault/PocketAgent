"""Deterministic action-authorization boundry.

Even if tool exists, is action allowed?

M03 policy: (26 Sep 2026 21:57)
    only READ_ONLY capabilities are permitted.
    
Later versions can introduce:
    - approvals
    - identities
    - capability scopes
    - risk levels
    - sandbox polices
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pocketagent.runtime.contracts.tools import ToolCallProposal
from pocketagent.runtime.tools.base import RuntimeTool, ToolEffect

@dataclass(frozen=True, slots=True) # slots - use array _slots instead of _dict
class GateDecision:
    """Result of deterministic action authorization.
    
    ActionGate will determine if allowed is True or False.
    """
    
    allowed: bool
    reason: str

class ActionGate(Protocol): # Strategy Pattern (Similar to PromptRenderer)
    """Policy interface for proposed runtime actions.
    
    Strategy Pattern - Have different concrete gate implementations for different strat
        - AllowAllActionGate
        - ReadOnlyActionGate
        - AllowlistActionGate
        - WorkspaceBoundaryGate
    """
    
    def evaluate( # pass in tool & proposal for evaluation
        self,
        *,
        tool: RuntimeTool[Any], 
        proposal: ToolCallProposal
    ) -> GateDecision:
        ...