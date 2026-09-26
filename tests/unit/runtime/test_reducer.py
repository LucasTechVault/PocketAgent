import pytest

from pocketagent.runtime.contracts import (
    ArtifactRef,
    BudgetLimits,
    BudgetState,
    Message,
    MessageRole,
    RunStatus,
    TraceContext,
)
from pocketagent.runtime.state.patch import RuntimeStatePatch
from pocketagent.runtime.state.reducer import (
    StateReductionError,
    reduce_state,
)
from pocketagent.runtime.state.state import RuntimeState


def make_state() -> RuntimeState:
    return RuntimeState(
        run_id="run-001",
        session_id="session-001",
        current_node="root",
        budget=BudgetState(
            limits=BudgetLimits(
                max_turns=20,
            ),
        ),
        trace=TraceContext(
            trace_id="trace-001",
        ),
    )


def test_reducer_appends_messages() -> None:
    state = make_state()

    message = Message(
        message_id="msg-001",
        role=MessageRole.USER,
        content="Hello",
    )

    next_state = reduce_state(
        state,
        RuntimeStatePatch(
            messages_append=[message],
        ),
    )

    assert state.messages == []
    assert next_state.messages == [message]


def test_reducer_upserts_artifacts() -> None:
    state = make_state()

    artifact = ArtifactRef(
        artifact_id="artifact-001",
        uri="file:///tmp/result.txt",
        media_type="text/plain",
    )

    next_state = reduce_state(
        state,
        RuntimeStatePatch(
            artifacts_upsert={
                artifact.artifact_id: artifact,
            },
        ),
    )

    assert state.artifacts == {}

    assert next_state.artifacts[
        "artifact-001"
    ] == artifact


def test_reducer_shallow_merges_working_memory() -> None:
    state = make_state()

    first_state = reduce_state(
        state,
        RuntimeStatePatch(
            working_memory_upsert={
                "goal": "research agent runtimes",
            },
        ),
    )

    second_state = reduce_state(
        first_state,
        RuntimeStatePatch(
            working_memory_upsert={
                "status": "investigating",
            },
        ),
    )

    assert second_state.working_memory == {
        "goal": "research agent runtimes",
        "status": "investigating",
    }


def test_reducer_replaces_scalar_fields() -> None:
    state = make_state()

    next_state = reduce_state(
        state,
        RuntimeStatePatch(
            step=1,
            current_node="reason",
            status=RunStatus.WAITING,
        ),
    )

    assert next_state.step == 1
    assert next_state.current_node == "reason"
    assert next_state.status is RunStatus.WAITING


def test_reducer_does_not_allow_step_to_move_backwards() -> None:
    state = reduce_state(
        make_state(),
        RuntimeStatePatch(
            step=5,
        ),
    )

    with pytest.raises(StateReductionError):
        reduce_state(
            state,
            RuntimeStatePatch(
                step=4,
            ),
        )


def test_reducer_preserves_run_identity() -> None:
    state = make_state()

    next_state = reduce_state(
        state,
        RuntimeStatePatch(
            step=1,
        ),
    )

    assert next_state.run_id == state.run_id
    assert next_state.session_id == state.session_id
    assert next_state.state_version == state.state_version