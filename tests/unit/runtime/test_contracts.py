import pytest
from pydantic import ValidationError

from pocketagent.runtime.contracts import (
    ArtifactRef,
    BudgetLimits,
    BudgetState,
    BudgetUsage,
    Message,
    MessageRole,
    RunStatus,
    ToolCallProposal,
    ToolCallRecord,
    ToolCallStatus,
    ToolError,
    ToolResult,
    TraceContext,
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
                max_tool_calls=40,
                max_wall_ms=90_000,
            ),
        ),
        trace=TraceContext(
            trace_id="trace-001",
        ),
    )


def test_valid_initial_runtime_state() -> None:
    state = make_state()

    assert state.state_version == 1
    assert state.step == 0
    assert state.status is RunStatus.RUNNING
    assert state.messages == []
    assert state.tool_calls == []


def test_runtime_state_rejects_negative_step() -> None:
    with pytest.raises(ValidationError):
        RuntimeState(
            run_id="run-001",
            current_node="root",
            step=-1,
            budget=BudgetState(
                limits=BudgetLimits(
                    max_turns=20,
                ),
            ),
            trace=TraceContext(
                trace_id="trace-001",
            ),
        )


def test_runtime_state_rejects_unknown_field() -> None:
    data = {
        "run_id": "run-001",
        "current_node": "root",
        "budget": {
            "limits": {
                "max_turns": 20,
            },
        },
        "trace": {
            "trace_id": "trace-001",
        },
        "magic_field": "not allowed",
    }

    with pytest.raises(ValidationError):
        RuntimeState.model_validate(
            data,
        )


def test_runtime_state_json_round_trip() -> None:
    state = make_state()

    encoded = state.model_dump_json()

    restored = RuntimeState.model_validate_json(
        encoded,
    )

    assert restored == state


def test_budget_usage_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        BudgetUsage(
            turns_used=-1,
        )


def test_artifact_key_must_match_artifact_id() -> None:
    artifact = ArtifactRef(
        artifact_id="artifact-001",
        uri="file:///tmp/report.txt",
        media_type="text/plain",
    )

    with pytest.raises(ValidationError):
        RuntimeState(
            run_id="run-001",
            current_node="root",
            artifacts={
                "wrong-key": artifact,
            },
            budget=BudgetState(
                limits=BudgetLimits(
                    max_turns=20,
                ),
            ),
            trace=TraceContext(
                trace_id="trace-001",
            ),
        )


def test_successful_tool_record_requires_result() -> None:
    proposal = ToolCallProposal(
        call_id="call-001",
        tool_name="read_file",
        arguments={
            "path": "README.md",
        },
    )

    with pytest.raises(ValidationError):
        ToolCallRecord(
            proposal=proposal,
            status=ToolCallStatus.SUCCEEDED,
        )


def test_tool_result_call_id_must_match_proposal() -> None:
    proposal = ToolCallProposal(
        call_id="call-001",
        tool_name="read_file",
    )

    result = ToolResult(
        call_id="call-999",
        output="contents",
    )

    with pytest.raises(ValidationError):
        ToolCallRecord(
            proposal=proposal,
            status=ToolCallStatus.SUCCEEDED,
            result=result,
        )