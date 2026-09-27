import asyncio
from pathlib import Path

from pocketagent.runtime.contracts.tools import (
    ToolCallProposal,
)
from pocketagent.runtime.tools.repository import (
    build_read_only_repository_tool_runtime,
)


async def main() -> None:

    tool_runtime = (
        build_read_only_repository_tool_runtime(
            Path.cwd()
        )
    )

    proposal = ToolCallProposal(
        call_id="smoke-001",
        tool_name="find_files",
        arguments={
            "pattern": "*.py",
            "path": "src",
            "max_results": 20,
        },
    )

    records = await tool_runtime.execute_all(
        [proposal]
    )

    for record in records:
        print(
            record.model_dump_json(
                indent=2
            )
        )


if __name__ == "__main__":
    asyncio.run(main())