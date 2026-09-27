from __future__ import annotations

import asyncio
import os
from pathlib import Path

from uuid import uuid4

from pocketagent.runtime import (
    BasicPromptRenderer,
    ControlLoop,
    RuntimeState,
    RuntimeStep,
    VLLMModelGateway
)

from pocketagent.runtime.contracts import (
    BudgetLimits, BudgetState,
    Message, MessageRole,
    TraceContext
)

from pocketagent.runtime.tools.repository import (
    build_read_only_repository_tool_runtime
)

SYSTEM_PROMPT = """
You are PocketAgent, a repository analysis worker.

Your task is to investigate the repository using the available
read-only tools and produce a grounded technical explanation.

Rules:

1. Inspect repository evidence before making claims.
2. Prefer search / find operations before reading large files.
3. Use targeted file reads when possible.
4. Cite relevant repository paths in the final answer.
5. Distinguish observed facts from inference.
6. Do not invent files, symbols, dependencies, or behavior.
7. If evidence is insufficient, say what is missing.
8. Continue using tools until you have enough evidence.
9. When you have enough evidence, stop calling tools and provide the final explanation.
""".strip()

USER_QUESTION = """
Explain how PocketAgent's minimal agent runtime works.

Identify the relevant source files and explain how:

- ControlLoop
- RuntimeStep
- ModelGateway
- PromptRenderer
- RuntimeStatePatch
- Reducer
- ToolRuntime

interact with one another.

Inspect the repository before answering.
""".strip()

async def main() -> None:
    
    repo_root = Path.cwd()
    
    base_url = os.getenv(
        "POCKET_AGENT_VLLM_BASE_URL",
        "http://127.0.0.1:8000/v1"
    )
    
    model_id = os.environ["POCKETAGENT_MODEL_ID"]

    # Tool subsystem
    tool_runtime = build_read_only_repository_tool_runtime(repo_root)
    
    # Initial runtime
    initial_state = RuntimeState(
        run_id=f"run-{uuid4()}",
        current_node="model",
        
        messages=[
            Message(
                message_id="user-001",
                role=MessageRole.USER,
                content=USER_QUESTION
                )
            ],
            budget=BudgetState(
                limits=BudgetLimits(
                        max_turns=8,
                        max_tool_calls=20
                    )
            ),
            trace=TraceContext(trace_id=f"trace-{uuid4()}")
    )

    # Prompt Strategy
    renderer = BasicPromptRenderer(
        system_prompt=SYSTEM_PROMPT,
        prompt_version="m03-repo-agent-v1"
    )
    
    # Model + Runtime
    async with VLLMModelGateway(base_url=base_url) as gateway:
        
        runtime_step = RuntimeStep(
            model_gateway=gateway,
            prompt_renderer=renderer,
            model_id=model_id,
            tool_runtime=tool_runtime,
            max_output_tokens=768
        )
        
        control_loop = ControlLoop(runtime_step=runtime_step)
        
        final_state = await control_loop.run(initial_state)
    
    # ------------------------------------------------------------
    # Inspect final trajectory
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("POCKETAGENT M03 REPOSITORY WORKER")
    print("=" * 80)

    print(
        f"STATUS: {final_state.status.value}"
    )

    print(
        f"STEPS: {final_state.step}"
    )

    print(
        "MODEL TURNS: "
        f"{final_state.budget.usage.turns_used}"
    )

    print(
        "TOOL CALLS: "
        f"{final_state.budget.usage.tool_calls_used}"
    )

    print(
        "INPUT TOKENS: "
        f"{final_state.budget.usage.input_tokens_used}"
    )

    print(
        "OUTPUT TOKENS: "
        f"{final_state.budget.usage.output_tokens_used}"
    )

    print()
    print("=" * 80)
    print("TOOL TRAJECTORY")
    print("=" * 80)

    for record in final_state.tool_calls:

        print()
        print(
            f"TOOL: {record.proposal.tool_name}"
        )

        print(
            f"STATUS: {record.status.value}"
        )

        print(
            f"ARGS: {record.proposal.arguments}"
        )

        if record.result is not None:
            print(
                f"RESULT: {record.result.output}"
            )

        if record.error is not None:
            print(
                f"ERROR: {record.error.code} "
                f"- {record.error.message}"
            )

    print()
    print("=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)

    assistant_messages = [
        message
        for message in final_state.messages
        if message.role is MessageRole.ASSISTANT
    ]

    if assistant_messages:
        print(
            assistant_messages[-1].content
        )

    else:
        print(
            "No final assistant response was produced."
        )


if __name__ == "__main__":
    asyncio.run(main())