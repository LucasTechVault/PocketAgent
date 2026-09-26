"""Prompt rendering boundary for PocketAgent

M02 responsibility 26 Sep 2026 08:46
Convert runtime-visible conversation information into messages that will
be sent to model.

PromptRenderer answers:
    "How should information be presented to the model?"

It does not answer:
    "Which information should the model see?" - For ContextManager
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pocketagent.runtime.contracts.common import (
    Message
)

from pocketagent.runtime.state.state import RuntimeState

@runtime_checkable
class PromptRenderer(Protocol):
    """Runtime-facing interface contract for prompt rendering.
    
    Future implementations may render prompts differently without changing
    ControlLoop.
    
    ModelGateway - Adapter pattern
    PromptRenderer - Stratetgy pattern
    
    Implementations:
        - Prompt Strategy
            - Sliding-window history
            - RAG injection
            - ReAct vs Plan & Execute
        - Task Workflow
            - BasicPromptRenderer
            - CodingPromptRenderer
            - ResearchPromptRenderer
            - ComputerUsePromptRenderer
        - Context Window Management
    """
    
    def render(self, state: RuntimeState) -> list[Message]:
        """Render model-visible messages from current runtime state."""
        ...