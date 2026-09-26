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
