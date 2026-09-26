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
    Message,
    MessageRole
)

from pocketagent.runtime.state import RuntimeState

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
        - Context Window Management
    """
    
    def render(self, state: RuntimeState) -> list[Message]:
        """Render model-visible messages from current runtime state."""
        ...

class BasicPromptRenderer:
    """Minimal M02 prompt renderer.
    
    Prepends fixed system instruction to existing runtime message history.
    
    This is intentionally simple.
    Context Selection, trimming, summarization, retrieval, token budgeting in M04.
    """
    
    def __init__(
        self,
        *,
        system_prompt: str,
        prompt_version: str = "m02-v1"
    ) -> None:
        if not system_prompt.strip():
            raise ValueError("system_prompt must not be empty.")
    
        if not prompt_version.strip():
            raise ValueError("prompt_version must not be empty.")
    
        self._system_prompt = system_prompt
        self._prompt_version = prompt_version
        
    
    def render(self, state: RuntimeState) -> list[Message]:
        """Produce messages for one model invocation."""
        
        system_message = Message(
            message_id = f"prompt:{self._prompt_version}",
            role=MessageRole.SYSTEM,
            content=self._system_prompt,
            metadata={
                "prompt_version": self._prompt_version
            }
        )
        
        return [
            system_message,
            *state.messages
        ]