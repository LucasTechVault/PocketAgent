import asyncio
import os
from uuid import uuid4

from pocketagent.runtime import (
    BasicPromptRenderer,
    ControlLoop,
    RuntimeState,
    RuntimeStep,
    VLLMModelGateway,
)

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


async def main() -> None:
    base_url = os.getenv(
        "POCKETAGENT_VLLM_BASE_URL",
        "http://127.0.0.1:8000/v1",
    )

    model_id = os.environ[
        "POCKETAGENT_MODEL_ID"
    ]

    initial_state = RuntimeState(
        run_id=f"run-{uuid4()}",
        current_node="model",
        messages=[
            Message(
                message_id="user-001",
                role=MessageRole.USER,
                content=(
                    "Explain what an Agent Runtime "
                    "Control Loop does in two sentences."
                ),
            )
        ],
        budget=BudgetState(
            limits=BudgetLimits(
                max_turns=3,
            ),
        ),
        trace=TraceContext(
            trace_id=f"trace-{uuid4()}",
        ),
    )

    renderer = BasicPromptRenderer(
        system_prompt=(
            "You are PocketAgent. "
            "Answer clearly and concisely."
        ),
        prompt_version="m02-v1",
    )

    async with VLLMModelGateway(
        base_url=base_url,
    ) as gateway:

        runtime_step = RuntimeStep(
            model_gateway=gateway,
            prompt_renderer=renderer,
            model_id=model_id,
            max_output_tokens=256,
        )

        control_loop = ControlLoop(
            runtime_step=runtime_step,
        )

        final_state = await control_loop.run(
            initial_state
        )

    print(
        "STATUS:",
        final_state.status,
    )

    print(
        "STEP:",
        final_state.step,
    )

    print(
        "TURNS:",
        final_state.budget.usage.turns_used,
    )

    print(
        "INPUT TOKENS:",
        final_state.budget.usage.input_tokens_used,
    )

    print(
        "OUTPUT TOKENS:",
        final_state.budget.usage.output_tokens_used,
    )

    print()

    for message in final_state.messages:
        print(
            f"{message.role.value}: "
            f"{message.content}"
        )


if __name__ == "__main__":
    asyncio.run(main())