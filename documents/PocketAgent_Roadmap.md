# PocketAgent Roadmap

## Pocket Agent Implementation Roadmap

```
PHASE A — Build the Runtime
              ↓
PHASE B — Build Single-Agent Intelligence
              ↓
PHASE C — Convert into a Coding Agent
              ↓
PHASE D — Harden into real Agent System
```

## Phase A Milestones:

| Milestone                                    | What you build                                                         | Main thing you learn                         |
| -------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------- |
| **M00 — Bootstrap**                          | Python project, `uv`, CLI entrypoint, config, lint/type/test tooling   | Engineering environment only                 |
| **M01 — Runtime Contracts**                  | `RuntimeState`, model/tool/result/budget/trace types, reducers         | **State and ownership boundaries**           |
| **M02 — Minimal Control Loop**               | Manual `while` loop, ModelGateway, PromptRenderer, hard turn limit     | **What actually makes an agent a runtime**   |
| **M03 — Tool Runtime + Action Gate**         | Registry, schemas, validation, execution, receipts, errors             | **Model proposal ≠ authority**               |
| **M04 — Context Management**                 | Context selection, token accounting, artifacts, compaction             | **State ≠ context**                          |
| **M05 — Persistence + Replay**               | Checkpoints, state version, resume, event/trajectory log               | **Durable agents**                           |
| **M06 — Topology + Termination**             | Legal transitions, explicit stop states, budgets, cancellation         | **Control flow ≠ reasoning**                 |
| **M07 — Runtime Evaluation + Observability** | Scenario harness, traces, latency/cost/tool metrics                    | **How to prove a runtime works**             |
| **M08 — Action Selection + Task State**      | `ActionProposal`, `TaskBeliefState`, `StatePatch`                      | **Beginning of Single Agent**                |
| **M09 — Planning + Progress**                | Optional plan, subgoals, acceptance criteria, fact/hypothesis tracking | **Task reasoning vs runtime orchestration**  |
| **M10 — Recovery**                           | Retry/replan/reconcile/clarify/escalate/refuse                         | **Agent resilience without infinite loops**  |
| **M11 — Coding-Agent Vertical Slice**        | repo/search/read/edit/shell/test/git tools                             | **Apply the generic architecture to coding** |
| **M12 — Operations / H100**                  | local model adapter, concurrency, cancellation, deployment, telemetry  | **Production agent engineering**             |
