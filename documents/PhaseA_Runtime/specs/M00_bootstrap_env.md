# M00 — Bootstrap Environment

## 1. Milestone Position

PocketAgent follows this implementation roadmap:

```text
PHASE A — Build the Runtime
              ↓
PHASE B — Build Single-Agent Intelligence
              ↓
PHASE C — Convert into a Coding Agent
              ↓
PHASE D — Harden into a Real Agent System
```

Phase A milestones:

| Milestone | What you build | Main thing you learn |
|---|---|---|
| M00 — Bootstrap | Python project, `uv`, CLI entrypoint, config, lint/type/test tooling | Engineering environment only |
| M01 — Runtime Contracts | `RuntimeState`, model/tool/result/budget/trace types, reducers | State and ownership boundaries |
| M02 — Minimal Control Loop | Manual while loop, `ModelGateway`, `PromptRenderer`, hard turn limit | What actually makes an agent a runtime |
| M03 — Tool Runtime + Action Gate | Registry, schemas, validation, execution, receipts, errors | Model proposal ≠ authority |
| M04 — Context Management | Context selection, token accounting, artifacts, compaction | State ≠ context |
| M05 — Persistence + Replay | Checkpoints, state version, resume, event/trajectory log | Durable agents |
| M06 — Topology + Termination | Legal transitions, explicit stop states, budgets, cancellation | Control flow ≠ reasoning |
| M07 — Runtime Evaluation + Observability | Scenario harness, traces, latency/cost/tool metrics | How to prove a runtime works |
| M08 — Action Selection + Task State | `ActionProposal`, `TaskBeliefState`, `StatePatch` | Beginning of Single Agent |
| M09 — Planning + Progress | Optional plan, subgoals, acceptance criteria, fact/hypothesis tracking | Task reasoning vs runtime orchestration |
| M10 — Recovery | Retry/replan/reconcile/clarify/escalate/refuse | Agent resilience without infinite loops |
| M11 — Coding-Agent Vertical Slice | repo/search/read/edit/shell/test/git tools | Apply the generic architecture to coding |
| M12 — Operations / H100 | local model adapter, concurrency, cancellation, deployment, telemetry | Production agent engineering |

M00 exists only to create the engineering foundation required for the milestones that follow.

---

## 2. Purpose

Bootstrap the smallest clean, reproducible Python project required to begin implementing PocketAgent.

At the end of M00, PocketAgent should:

- install reproducibly;
- expose a minimal CLI;
- load application configuration;
- provide logging;
- support linting and formatting;
- support static type checking;
- support automated tests;
- run on the local development machine without an LLM, GPU, database, or external service;
- be ready for M01 — Runtime Contracts.

M00 does **not** implement an agent.

---

## 3. Learning Objective

The learning objective of M00 is intentionally narrow:

> Establish a reliable software-engineering environment before introducing Agent Runtime concepts.

M00 should teach or reinforce:

- Python project structure;
- dependency and environment management;
- package boundaries;
- CLI packaging;
- configuration hygiene;
- test/lint/type-check workflows;
- reproducible developer verification.

Agent Runtime architecture begins in **M01**, not M00.

---

## 4. Engineering Mode

### M00

Agentic engineering is allowed for M00 because the work is limited to boilerplate environment bootstrap.

It may be used to create:

- `pyproject.toml`;
- package directories;
- CLI bootstrap;
- configuration bootstrap;
- logging bootstrap;
- test harness;
- lint/type/test configuration;
- `.gitignore`;
- `.env.example`;
- minimal README setup instructions.

### M01 onward

From M01 onward, implementation becomes **manual, AI-assisted engineering**.

The developer should:

1. study the concept being implemented;
2. decide the required contracts and boundaries;
3. create the relevant files/modules;
4. write or deliberately copy small pieces of code;
5. understand every state transition, interface, and ownership boundary;
6. use AI primarily for explanation, review, debugging, and focused implementation assistance.

The project must not use autonomous generation to skip the implementation knowledge that each milestone is intended to teach.

---

## 5. Scope

M00 includes only:

- Python project initialization;
- `uv` environment and dependency management;
- package installation;
- minimal CLI entrypoint;
- configuration/environment handling;
- basic application logging;
- Ruff formatting/linting;
- mypy static typing;
- pytest test harness;
- repository hygiene;
- smoke tests;
- developer verification commands.

---

## 6. Explicit Non-Goals

M00 must **not** implement any of the following:

- `RuntimeState`;
- reducers;
- model request/response contracts;
- `ModelGateway`;
- provider SDK integration;
- prompts or prompt rendering;
- agent control loop;
- tools or tool registry;
- tool execution;
- action gates;
- context management;
- persistence/checkpointing;
- topology;
- runtime termination policy;
- evaluation harness;
- tracing system;
- `ActionProposal`;
- `TaskBeliefState`;
- planning;
- recovery;
- coding-agent tools;
- MCP;
- RAG;
- LangGraph;
- OpenAI Agents SDK;
- Temporal;
- local model serving;
- H100 configuration.

Those concepts must be introduced only when their corresponding milestone is reached.

---

## 7. Development Environments

### Local development

Primary bootstrap environment:

- macOS;
- Apple Silicon;
- M4 Max;
- 64 GB unified memory.

This machine will initially be used for:

- architecture implementation;
- unit tests;
- CLI development;
- runtime development;
- local integration tests.

### Future remote environment

Future infrastructure includes:

- Linux;
- 2 × NVIDIA H100 NVL;
- remotely shared compute.

M00 does not configure GPU infrastructure.

However, the project should avoid unnecessary macOS-specific assumptions so that later milestones can run on Linux without restructuring the core package.

---

## 8. Required Toolchain

Required tools:

- Git;
- Python 3.12;
- `uv`.

Verify:

```bash
git --version
python3 --version
uv --version
```

The project should not depend on the system Python environment after initialization.

---

## 9. Dependency Management

`uv` is the canonical environment and dependency manager for PocketAgent.

Canonical files:

```text
pyproject.toml
uv.lock
```

Environment synchronization:

```bash
uv sync
```

Commands should normally execute through:

```bash
uv run <command>
```

Examples:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

Do not maintain parallel dependency-management systems unless a later deployment requirement explicitly needs an exported format.

---

## 10. Minimal Repository Structure

M00 should create only the structure required to bootstrap the project.

```text
PocketAgent/
│
├── docs/
│
├── documents/
│   ├── PhaseA_Runtime/
│   │   └── specs/
│   │       └── M00_bootstrap_env.md
│   ├── PhaseB_SingleAgent/
│   ├── PhaseC_CodingAgent/
│   ├── PhaseD_AgentSystem/
│   └── PocketAgent_Roadmap.md
│
├── src/
│   └── pocketagent/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       └── logging.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

Do **not** create empty future architecture modules such as:

```text
runtime/
state/
tools/
model/
context/
topology/
persistence/
```

during M00.

Those modules should appear only when the relevant milestone is implemented.

---

## 11. Python Package

The Python package name is:

```text
pocketagent
```

Use a `src` layout:

```text
src/pocketagent/
```

Imports must resolve through the installed package.

Preferred:

```python
from pocketagent.config import Settings
```

Avoid repository path manipulation such as:

```python
import sys

sys.path.append(...)
```

---

## 12. Minimal CLI

PocketAgent should expose:

```bash
pocketagent
```

Required commands:

```bash
pocketagent --help
pocketagent version
```

A small environment diagnostic command may also be included:

```bash
pocketagent doctor
```

Example:

```text
$ pocketagent doctor

PocketAgent Environment
Python:        3.12.x
Package:       OK
Configuration: OK
Status:        READY
```

The CLI must not call an LLM during M00.

---

## 13. Configuration

Configuration should be centralized in:

```text
src/pocketagent/config.py
```

M00 only needs enough configuration to prove the mechanism works.

Initial variables:

```text
POCKETAGENT_ENV
POCKETAGENT_LOG_LEVEL
```

Example:

```bash
POCKETAGENT_ENV=development
POCKETAGENT_LOG_LEVEL=INFO
```

Future configuration categories such as runtime, model, tool, persistence, and observability settings should **not** be designed yet.

---

## 14. Environment Files and Secrets

The repository may contain:

```text
.env.example
```

Example:

```env
POCKETAGENT_ENV=development
POCKETAGENT_LOG_LEVEL=INFO
```

The repository must not commit:

```text
.env
```

Never commit:

- API keys;
- model provider credentials;
- passwords;
- access tokens;
- SSH keys;
- cloud credentials.

Actual model credentials are not needed in M00.

---

## 15. Logging

Create one minimal application logging bootstrap.

Expected capabilities:

- configurable log level;
- timestamp;
- severity;
- module/logger name;
- message.

Normal application code should use:

```python
logger = logging.getLogger(__name__)
```

rather than relying on ad-hoc `print()` statements for operational logging.

Structured runtime telemetry is a later concern, primarily M07.

Do not over-engineer logging in M00.

---

## 16. Initial Dependencies

Keep dependencies intentionally small.

### Runtime

Suggested:

```text
typer
pydantic
pydantic-settings
```

Each dependency must have a concrete M00 purpose.

### Development

Suggested:

```text
pytest
pytest-asyncio
ruff
mypy
```

`pytest-asyncio` may be included because later runtime components will likely use asynchronous interfaces.

Do not add agent frameworks during bootstrap.

---

## 17. Dependencies Explicitly Deferred

Do not install merely for future convenience:

```text
langchain
langgraph
openai-agents
mcp
temporal
vector database clients
GPU inference frameworks
```

They should be introduced only after the architecture requires them and after the underlying concept has been understood.

---

## 18. `pyproject.toml` Responsibilities

`pyproject.toml` should define:

- project metadata;
- package name;
- project version;
- supported Python version;
- runtime dependencies;
- development dependencies;
- CLI script entrypoint;
- Ruff configuration;
- mypy configuration;
- pytest configuration.

Conceptually:

```text
pyproject.toml
├── project
├── dependencies
├── dev dependencies
├── scripts
├── ruff
├── mypy
└── pytest
```

No Agent Runtime configuration belongs here yet.

---

## 19. Code Quality Commands

### Format

```bash
uv run ruff format .
```

### Verify formatting

```bash
uv run ruff format --check .
```

### Lint

```bash
uv run ruff check .
```

### Type check

```bash
uv run mypy src
```

### Test

```bash
uv run pytest
```

All checks must pass before M00 is complete.

---

## 20. Minimum Tests

M00 requires only enough tests to prove the engineering harness works.

### Package import

Verify:

```python
import pocketagent
```

### Configuration

Verify:

- defaults can load;
- environment variables override defaults.

### CLI

Verify that:

```bash
pocketagent --help
```

returns successfully.

Optionally verify:

```bash
pocketagent version
pocketagent doctor
```

Do not write tests for runtime behavior that does not yet exist.

---

## 21. Canonical Verification Sequence

The repository should support the following workflow:

```bash
uv sync

uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

A wrapper such as:

```bash
make verify
```

or:

```bash
./scripts/verify.sh
```

should be added only if it provides enough value to justify another layer.

For M00, direct commands are sufficient.

---

## 22. Clean-Checkout Smoke Test

A new developer should be able to perform:

```bash
git clone <repository>
cd PocketAgent

uv sync

uv run pocketagent --help
uv run pocketagent doctor

uv run ruff check .
uv run mypy src
uv run pytest
```

without requiring:

- an API key;
- an LLM;
- a database;
- a GPU;
- the H100 machines;
- any external service.

---

## 23. Cross-Platform Constraint

M00 must avoid unnecessary assumptions about:

- Homebrew paths;
- macOS-only filesystem paths;
- Apple-specific binaries;
- Metal availability;
- NVIDIA drivers;
- GPU presence.

The intended evolution is:

```text
M4 Max local development
          ↓
generic Linux-compatible PocketAgent
          ↓
remote H100-backed model infrastructure
```

Changing inference hardware later should not require reorganizing the core application.

---

## 24. Git Hygiene

`.gitignore` should at minimum cover:

```text
.venv/
.env
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
dist/
build/
*.egg-info/
```

Repository secrets must remain outside source control.

---

## 25. README Requirements

After M00, `README.md` should minimally explain:

- what PocketAgent is;
- the four project phases;
- current phase;
- current milestone;
- prerequisites;
- setup with `uv`;
- how to run the CLI;
- how to run verification.

Suggested status block:

```text
Current Phase: Phase A — Build the Runtime
Current Milestone: M00 — Bootstrap
```

---

## 26. Deferred Architecture Decisions

M00 deliberately does **not** decide:

- hosted model provider;
- local model choice;
- inference server;
- H100 serving stack;
- model routing;
- graph/orchestration framework;
- runtime persistence database;
- MCP usage;
- sandbox implementation;
- tool authorization model;
- context compression strategy;
- tracing backend;
- evaluation platform;
- long-running workflow engine.

These decisions should be made in the milestone where their architectural need becomes concrete.

---

## 27. Acceptance Criteria

### Environment

- [ ] Python 3.12 is used.
- [ ] Environment and dependencies are managed with `uv`.
- [ ] `uv sync` succeeds from a clean checkout.
- [ ] `uv.lock` exists.

### Package

- [ ] `src/pocketagent/` exists.
- [ ] `import pocketagent` succeeds.
- [ ] Package version is available.

### CLI

- [ ] `uv run pocketagent --help` succeeds.
- [ ] `uv run pocketagent version` succeeds.
- [ ] `uv run pocketagent doctor` succeeds if implemented.

### Configuration

- [ ] Configuration loads successfully.
- [ ] Environment variables override defaults.
- [ ] `.env.example` exists.
- [ ] `.env` is ignored.

### Engineering Quality

- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run mypy src` passes.
- [ ] `uv run pytest` passes.

### Portability

- [ ] No mandatory macOS-specific application dependency exists.
- [ ] No GPU is required.
- [ ] No external service is required.

### Milestone Boundary

- [ ] No `RuntimeState`.
- [ ] No model integration.
- [ ] No control loop.
- [ ] No tool runtime.
- [ ] No persistence subsystem.
- [ ] No agent framework.
- [ ] No single-agent behavior.
- [ ] No coding-agent implementation.

---

## 28. Definition of Done

M00 is complete when this sequence works from a fresh checkout:

```text
clone repository
       ↓
uv sync
       ↓
PocketAgent package installs
       ↓
CLI starts
       ↓
configuration loads
       ↓
format/lint passes
       ↓
type checking passes
       ↓
tests pass
```

At that point the bootstrap phase stops.

No additional architecture should be added under the justification of “we will need it later.”

The next milestone is:

```text
M01 — Runtime Contracts
```

M01 is the first milestone that implements actual Agent Runtime concepts:

```text
RuntimeState
model/tool/result contracts
BudgetState
TraceContext
reducers
state invariants
ownership boundaries
```

Those components must be implemented manually and deliberately so that their role in the Agent Runtime is understood before proceeding to M02.
