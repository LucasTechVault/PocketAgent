#### M02 -> "How does the agent think / executes repeatedly?"

#### M03 -> "How does something the model wants to do become a controlled real-world action?"

Currently, Model (Qwen) can only say things, like a chatbot.

M03 -> Model begins acquiring **capabilities**

#### Danger:

```
ToolCallProposal
    ↓
execute immediately
```

#### Safe: (M03 Objective Flow)

**Model Proposes**
**Deterministic Runtime disposes**

```
ToolCallProposal
        ↓
   ToolRegistry
        ↓
   Does tool exist?
        ↓
 Schema Validation
        ↓
    Action Gate
        ↓
 Is it permitted?
        ↓
    ToolExecutor
        ↓
 deterministic function
        ↓
     ToolResult
        ↓
   ToolCallRecord
        ↓
 RuntimeStatePatch
        ↓
      Reducer

```

---

## M03 Scope (Read-only Repository Tools):

```
M03
├── Tool Registry
├── Tool Executor
├── Action Gate
├── argument/schema validation
├── result/error normalization
│
└── first real tools
    ├── list_directory
    ├── read_file
    ├── read_file_range
    ├── search_text
    └── find_files
```

**Out-of-Scope (For now):**

- writing code
- shell commands
- git commit
- file deletion

---

### Example Flow:

```
"Does this repository use Spring Boot?"
```

```
User question
    ↓
Qwen
    ↓
search_text("springframework")
    ↓
Tool Runtime
    ↓
observations
    ↓
Qwen
    ↓
read_file("build.gradle")
    ↓
Tool Runtime
    ↓
observations
    ↓
Qwen
    ↓
grounded explanation
```

---

### Changes required:

```
PocketAgent/
├── examples/
│   ├── m02_control_loop_smoke.py
│   ├── m03_tool_runtime_smoke.py          # deterministic tool test
│   └── m03_repo_agent_smoke.py            # Qwen + real repo tools
│
├── src/
│   └── pocketagent/
│       └── runtime/
│           ├── contracts/                  # M01
│           ├── model_gateway.py            # M02
│           ├── prompt.py                   # M02
│           ├── step.py                     # M02 → MODIFY for M03
│           ├── loop.py                     # M02, mostly unchanged
│           │
│           └── tools/                       # M03 ← NEW
│               ├── __init__.py
│               ├── base.py
│               ├── registry.py
│               ├── gate.py
│               ├── executor.py
│               ├── runtime.py
│               │
│               └── repository/
│                   ├── __init__.py
│                   ├── workspace.py
│                   └── tools.py
│
└── tests/
    └── unit/
        └── runtime/
            └── tools/
                ├── test_registry.py
                ├── test_gate.py
                ├── test_executor.py
                └── test_repository_tools.py

```

**M03 core intuition:**

```
base.py
    What IS a PocketAgent tool?

registry.py
    What tools exist?

gate.py
    Is this proposed action allowed?

executor.py
    Validate and actually invoke one allowed tool.

runtime.py
    Facade used by RuntimeStep.

repository/workspace.py
    What filesystem area is this worker allowed to inspect?

repository/tools.py
    Actual read-only repository capabilities.
```
