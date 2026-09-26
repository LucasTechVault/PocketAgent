import pytest

from pocketagent.runtime.contracts.budget import (
    BudgetLimits,
    BudgetState,
)
from pocketagent.runtime.contracts.common import (
    Message,
    MessageRole,
)
from pocketagent.runtime.contracts.trace import (
    TraceContext,
)
from pocketagent.runtime.prompt import (
    BasicPromptRenderer,
)
from pocketagent.runtime.state import RuntimeState


def make_state() -> RuntimeState:
    return RuntimeState(
        run_id="run-001",
        current_node="model",
        messages=[
            Message(
                message_id="msg-001",
                role=MessageRole.USER,
                content="Explain agent runtimes.",
            )
        ],
        budget=BudgetState(
            limits=BudgetLimits(
                max_turns=5,
            ),
        ),
        trace=TraceContext(
            trace_id="trace-001",
        ),
    )


def test_renderer_prepends_system_message() -> None:
    state = make_state()

    renderer = BasicPromptRenderer(
        system_prompt="You are PocketAgent.",
    )

    rendered = renderer.render(state)

    assert len(rendered) == 2

    assert rendered[0].role is MessageRole.SYSTEM
    assert rendered[0].content == "You are PocketAgent."

    assert rendered[1] == state.messages[0]


def test_renderer_preserves_message_order() -> None:
    state = make_state()

    renderer = BasicPromptRenderer(
        system_prompt="System instruction.",
    )

    rendered = renderer.render(state)

    assert rendered[1:] == state.messages


def test_renderer_does_not_mutate_runtime_state() -> None:
    state = make_state()

    original_messages = list(
        state.messages
    )

    renderer = BasicPromptRenderer(
        system_prompt="System instruction.",
    )

    renderer.render(state)

    assert state.messages == original_messages


def test_renderer_records_prompt_version() -> None:
    state = make_state()

    renderer = BasicPromptRenderer(
        system_prompt="System instruction.",
        prompt_version="m02-test-v2",
    )

    rendered = renderer.render(state)

    assert (
        rendered[0].metadata["prompt_version"]
        == "m02-test-v2"
    )


def test_renderer_rejects_empty_system_prompt() -> None:
    with pytest.raises(ValueError):
        BasicPromptRenderer(
            system_prompt="   ",
        )