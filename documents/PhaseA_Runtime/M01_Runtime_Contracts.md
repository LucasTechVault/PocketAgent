# M01 - Runtime Contracts

Define the vocab & laws that every future `runtime` component will speak.

**What are `runtime` components?**

- agent = business logic
- runtime components = middleware (execution)
  1. State Manager / Memory Store: safe read / write `RuntimeState`
  2. ToolExecutor (agent requests tool, this component actually executes it)
  3. Safety & Policy Enforcer
  4. Control Loop / Graph Engine
  5. Telemetry / Trajectory Logger

**4 Main Components:**

1. Application (Frontend + Backend)
2. Agent (AI that performs the reasoning)
   - Prompts
   - Parsers
   - Router
   - Model + Planning (semantic)
3. Agent Runtime (Thinking loop + Model Call + Tool Execution)
   - model call + tool execution + persistence + control loop (execution of planning)
4. Context (Supplementary info for agent) (3 RAG pipelines)

## M01 Focus: 8 Contract Concepts

1. Common primitive contracts
2. Model contracts
3. Tool contracts
4. Budget contracts
5. Trace contract
6. Termination state contract
7. Canonical RuntimeState
8. StatePatch + reducer

## 1. Common Primitive Contracts

Standardized shipping containers of agentic system.

- `RunStatus`: Absolute objective reality of system. [RUNNING, WAITING, COMPLETED, FAILED, CANCELLED]
- `Message`: Forces every external model to speak system's language rather than force system to speak model's language.
- `ArtifactRef`: Lightweight pointer to Artifact stored in db. Prevents transferring of large binaries across services

## 2. Model Contracts

Defines the objects shared between the Agent Runtime and Model Serving Engine.
This keeps model agnostic.

- `ModelRequest` (Data Contract): Everything the model needs to know at given instant to make a decision. Translated from system's rich internal state into clean, model-friendly format.
- `ModelResponse` (Data Contract): Model returning structured package after "thinking". Not just raw text.
- `ModelGateway` (Interface Contract): Does not expose any routes to users. It acts as private outbound client that runtime uses to call external services. Gateway will process & validate the response and send it back to runtime.

## 3. Tool Contracts

This separation is the single, most important security & reliability boundary in agent architecture. It represents the firewall between **non-deterministic intent** (What the AI wants to happen) and **deterministic reality** (what actually happened to the system).

- `ToolCallProposal`: The LLM generates a JSON payload, requesting an action. Nothing actually happened yet. This is like when a customer ordered their food.
- `ToolCallRecord`: Agent Runtime validates `ToolCallProposal`, assigns it a uuid, and logs it into state machine `PENDING` or `RUNNING`.
- `ToolResult`: The output from runtime's actual deterministic execution. The result will then be recorded to be passed back to Model for further analysis.
- `ToolError`: System prevented action. Runtime feeds ToolError back to LLM instead of throwing exception. This helps model decide next step.

## 4. Budget Contracts

Agent loops are potentially unbounded processes. In traditional software (e.g. REST API), function run once & returns a result & stops. Agents use `while` loops. If agent gets confused or encounters API error, it might get trapped in infinite loop.

Every model call costs real money & takes time. Infinite loop = catastrophic.

**Budget Contracts** -> Holds exactly how much money, time, tokens authorized agent to spend

- `BudgetLimits` (Data contract) Defines the absolute maximum resources agent is authorized to consume. (max_turns, max_tool_calls, max_wall_ms, max_input_tokens). Multiple dimensions because agent loop can spiral out of control in different ways.
- `BudgetUsage` (Data contract): Same shape as limits but tracks what actually happened. Processes metadata from `ModelGateway` / `ToolExecutor`
- `BudgetState` (Data contract): Wrapper for `BudgetLimits` and `BudgetUsage` into single obj.
- Termination policy -> Logic that reads usage & cuts the loop.

## 5. Trace Contract

When agentic system runs, it doesn't just do 1 thing. A single user prompt ("Fix this bug") can split into dozens of sub-actions:

- reasoning steps
- tool proposals
- tool executions
- state updates

`TraceContext`:

- trace_id: Master tracking number for a single workflow. Every action is stamped with trace_id for that workflow.
- parent_id: ID of specific operation that triggered current operation.
- correlation_id: optional id that links agent's internal trace to outside world operations

## 6. Termination Contract

When an agent run finally stops, the system needs an objective, standardized record of how and why run ended.

- `TerminationState`: Official report at the end of loop.

  - reason_code: SUCCESS, BUDGET_EXCEEDED, FATAL_ERROR, USER_CANCELLED etc.
  - detail: human-readable string or JSON obj explaining exact context of the stop.
  - requested: metadata field tracking who initiated termination (LLM reasoning or Runtime?)

- `TerminationPolicy` - Implementation of how TerminationState is populated.

## 7. Canonical `RuntimeState`

- Up till this point, all previous contracts have been individual pieces across the system.
- `RuntimeState` is the master ledger that wraps all those pieces into a single, unified snapshot.
- If a server loses power, this object contains the needed to troubleshoot.

```
RuntimeState
    state_version
    run_id - specific execution to user & conversation
    session_id

    step
    status
    current_node

    messages
    tool_calls
    artifacts
    working_memory

    budget
    termination
    trace
```

---

## Working Memory & TaskBeliefState

**`working_memory`:**

Blank whiteboard provided by Runtime (Landlord) to Agent (Tenant).
Landlord (Runtime) does not care / dictate what Agent does to whiteboard.

Whiteboard design can be:

- working_memory: `dict[str, Any]` : keep generic.
- `TaskBeliefState`: A more formal definition of working memory (whiteboard)

## RuntimeStatePatch & Reducer

`RuntimeStatePatch` + `RuntimeState` (existing) --> Reducer --> `RuntimeState` (new, updated)

- `RuntimeStatePatch`: Holds only the new information (the deltas)
- `RuntimeState`: Holds the current reality
- `Reducer`: Pure, predictable fn that applies the strict rules (Append, Merge, Replace)

---

**RuntimeStatePatch:**

1. Actor in system finishes its specific job.
2. Actor in system fills out `RuntimeStatePatch` with required data.
3. After filling it up, it hands it back to the RuntimeLoop.

Different components build different `RuntimeStatePatch` depending on what just happened.

    - ModelGateway (M02)
    - ToolExecutor (M03)
    - Control Loop (M06)
