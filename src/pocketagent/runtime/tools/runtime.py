"""Facade for PocketAgent's Tool Capability subsystem.

ToolRuntime is a sub-facade to RuntimeStep ControlLoop facade.

ControlLoop
|
RuntimeStep
    Coordinates 4 high-level collaborators
        1. PromptRenderer (Strategy Pattern)
        2. ModelGateway (Adapter Pattern)
        3. ToolRuntime (Sub-Facade)
            - ToolRegistry
            - ToolExecutor
        4. reduce_state() - state update
"""

from __future__ import annotations

from pocketagent.runtime.contracts.tools import (
    ToolCallProposal,
    ToolCallRecord,
    ToolDefinition
)

from pocketagent.runtime.tools.executor import ToolExecutor
from pocketagent.runtime.tools.registry import ToolRegistry

class ToolRuntime:
    """Single interface used by RuntimeStep"""
    
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        executor: ToolExecutor
    ) -> None:
        self._registry = registry
        self._executor = executor
        
    def definitions(self) -> list[ToolDefinition]:
        """Return model-visible tool schemas."""
        return self._registry.definitions()

    async def execute_all(self, proposals: list[ToolCallProposal]) -> list[ToolCallRecord]:
        """Execute proposals sequentially
        
        M03 intentionally avoids parallel execution. (26 Sep 2026 23:27)
        
        Parallel execution adds ordering, race, and side-effects concerns
        that belong in later runtime work.
        """
        
        records: list[ToolCallRecord] = []
        
        for proposal in proposals:
            records.append(await self._executor.execute(proposal))
        
        return records
        