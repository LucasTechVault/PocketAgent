# M02 Minimal Control Loop

- M01 defined the nouns.
- M02 introduces the verbs.

**M02 High Level Objective**

| Manual while loop + ModelGateway + PromptRenderer + hard turn limit

**Main Lesson:**
| What turns an LLM call into an agent runtime?
Answer:The loop around the model.

**Plain LLM Call:**

```
User
 ↓
Prompt
 ↓
Model
 ↓
Answer
```

**Agent Loop:**

```
RuntimeState
      ↓
construct request
      ↓
Model
      ↓
ModelResponse
      ↓
interpret response
      ↓
RuntimeStatePatch
      ↓
Reducer
      ↓
RuntimeState
      ↓
should continue?
      │
      └──────────────→ repeat
```

**M02 Key Implementation (5):**

```
M02
├── ModelGateway (1)
├── PromptRenderer (2)
├── Runtime step (3)
├── ControlLoop (4)
└── hard turn limit (5)
```

---

## 1. ModelGateway

`ModelGateway` is the anti-corruption layer between different vendor-specific reality of LLM providers and PocketAgent's clean, internal runtime contracts.

**ModelGateway Main Job:**

```
[ Your Runtime ]
       │  ModelRequest (PocketAgent contract)
       ▼
┌───────────────────────────────────────────────────────────┐
│ ModelGateway Implementation (e.g., OpenAIGateway, vLLM)   │
│                                                           │
│  1. Outbound Translation:                                 │
│     PocketAgent Messages/Tools ──► Provider JSON payload  │
│                                                           │
│  2. Transport:                                            │
│     Execute HTTP / gRPC call with timeouts & retries      │
│                                                           │
│  3. Inbound Translation:                                  │
│     Provider Raw JSON ──► Normalized ModelResponse        │
└───────────────────────────────────────────────────────────┘
       │  ModelResponse (PocketAgent contract)
       ▼
[ Your Runtime ]


Outbound Translate to different Provider JSON payload:
                  ModelGateway
                 /            \
                /              \
        Hosted adapter       H100 adapter
                            open-source model

                            ModelGateway (Protocol)
                         ┌───────────┴───────────┐
                         │   async def generate  │
                         └───────────┬───────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
HostedAdapter (e.g., Anthropic)                     H100Adapter (e.g., vLLM / SGLang)
┌──────────────────────────────────────┐            ┌──────────────────────────────────────┐
│ Outbound:                            │            │ Outbound:                            │
│ - pocket_msg.role == "developer"     │            │ - pocket_msg.role == "developer"     │
│   → move to top-level `system`       │            │   → map to `"system"` in chat dict   │
│ - tools → Anthropic `input_schema`   │            │ - tools → OpenAI `parameters` schema │
│                                      │            │                                      │
│ Transport:                           │            │ Transport:                           │
│ - `httpx.post("api.anthropic.com")`  │            │ - `httpx.post("http://h100:8000/v1")`│
│                                      │            │                                      │
│ Inbound:                             │            │ Inbound:                             │
│ - map `stop_reason == "tool_use"`    │            │ - map `finish_reason == "tool_calls"`│
│   → `ModelFinishReason.TOOL_CALL`    │            │   → `ModelFinishReason.TOOL_CALL`    │
└──────────────────────────────────────┘            └──────────────────────────────────────┘
```

Without gateway, control loop will fill up with vendor-specific `if/else` checks

- OpenAI nests tool calls under `response.choices[0].message.tool_calls[i].function.arguments`

- Anthropic puts tool calls as blocks in `response.context` with type `tool_use`

- local vLLM returns an OpenAI-compatible payload but handles finish reason differently ("stop" vs "tool_calls")

---

## 2. PromptRenderer (Formatting & Serialization)

How should selected information be formatted / instructed for model?

- How are instructions styled?
- Where does timestamp go?
- What is the template for system instructions?
- How are role boundaries serialized?

RuntimeState is everything the runtime know at that instant.
Model should not receive whole RuntimeState object.
A simple implements = system message + state.messages

**PromptRenderer:**

```
RuntimeState
     ↓
PromptRenderer
     ↓
list[Message]

system prompt + state.messages -> list[Message]
```

**Future Complexities / Considerations:**

1. ContextManager (M04)
2. RAG

**Importance of prompt version:**
For the purpose of evaluation tracking.

```
Qwen 3B
+
prompt v1
    → 58% success

Qwen 3B
+
prompt v2
    → 71% success
```

---

## 3. One runtime step

A runtime step is a single transaction inside the Control Loop.

> "How do we move safely from state N to state N+1?"

Scope:
Read -> Propose -> Reduce

**Patch & Reducer pattern:**

1. State immutability -> Never directly modified in-place. Only via Patch & Reducer.

2. Auditability -> Every single tick produces an explicit RuntimeStatePatch. If log initial state + list of patches, can perform replay.

3. Decoupled Business logic -> Step never directly alter state. It creates a proposal (RuntimeStatePatch) & executed + validated inside Reducer

```
CURRENT STATE
     ↓
build request
     ↓
call model
     ↓
receive response
     ↓
produce patch
     ↓
reduce
     ↓
NEXT STATE
```

---

## 4. Control Loop

The Control Loop is the lifecycle supervisor and process driver of `runtime`

> "When does execution begin / repeat / pause / terminate?"

Scope:
Initialize -> Guard / Check -> Advance (runtime_step) -> Enforce Termination

**Key Responsibility of Control Loop:**

1. Environmental Governance (Hard Limits & Invariants)
   Supervises execution boundaries before each step executes. If constraints (max turns / execution timeout / token budget) breached, loop bypass execution -> terminates

2. Dual-Path Termination Arbitration
   There can be 2 types of termination:

   - Semantic Termination (Agent-driven): Model indicates completion with answer.
   - Infrastructure Termination (Runtime-driven): Supervisor intervenes and forces execution to stop due to resource limits / cancellation signals / unrecoverable exceptions

3. Lifecycle Orchestration (Checkpointing & Suspension)

   - Coordinates mid-run persistence (M05: Checkpointing)
   - human-in-the-loop interruptions (pausing to await approval)
   - final state consolidation

```
INITIAL STATE
     │
     ▼
┌───────────────────────────────┐
│   Check Termination Policy    │◄─────────────────┐
│  - max_turns exceeded?        │                  │
│  - budget / deadline hit?     │                  │
│  - status != RUNNING?         │                  │
└──────────────┬────────────────┘                  │
               │                                   │
      ┌────────┴────────┐                          │
     YES                NO                         │
      │                 │                          │
      ▼                 ▼                          │
Force Termination   Execute `run_step(state)`      │
Patch & Reduce          │                          │
      │                 ▼                          │
      │             NEXT STATE                     │
      │                 │                          │
      │                 └──────────────────────────┘
      ▼
TERMINAL STATE
```

---

## 5. Hard Turn Limit

The safety boundary of runtime (supervisor)

**Core Runtime Principle:**

> The model proposes. The runtime disposes.
> LLM never has the authority to decide it may run forever.
> Runtime decides when to stop.

**Key Concepts:**

1. Preemptive Guard (Check before Execute)

   Limits are evaluated before starting next step.
   If limits exceeded, execution skipped.

2. Deterministic & Invariant

   Hard turn limit is entirely deterministic.
   It is specified by the engineer and cannot be bypassed / hallucinated.
   No negatiation with model.

## M02 trajectory:

```
            RuntimeState(step=0)
                     │
                     ▼
               PromptRenderer
                     │
                     ▼
                ModelRequest
                     │
                     ▼
                ModelGateway
                     │
                     ▼
               ModelResponse
             "An agent runtime..."
                     │
                     ▼
            RuntimeStatePatch
        append assistant message
        increment turn usage
        increment step
                     │
                     ▼
                  reducer
                     │
                     ▼
             RuntimeState(step=1)
```

### M02 Summary:

```
model_gateway.py
"How do I communicate with inference?"

prompt.py
"How do I present information to the model?"

step.py
"How do I advance state exactly once?"

loop.py
"Am I allowed to advance again?"
```
