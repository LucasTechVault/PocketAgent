# PocketAgent

PocketAgent is a milestone-driven learning project for building an agent runtime,
adding single-agent intelligence, turning it into a coding agent, and hardening
it into an operational system.

The four project phases are:

1. **Phase A — Build the Runtime**
2. **Phase B — Build Single-Agent Intelligence**
3. **Phase C — Convert into a Coding Agent**
4. **Phase D — Harden into a Real Agent System**

**Current Phase:** Phase A — Build the Runtime

**Current Milestone:** M00 — Bootstrap

M00 provides the engineering environment, configuration, logging, and a minimal
CLI. See the [M00 specification](documents/PhaseA_Runtime/specs/M00_bootstrap_env.md)
and [project roadmap](documents/PocketAgent_Roadmap.md). The next milestone is
M01 — Runtime Contracts.

## Prerequisites

- Git
- Python 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

Check your tools:

```bash
git --version
python3 --version
uv --version
```

The project selects Python 3.12 through `.python-version` and `pyproject.toml`,
even if your system `python3` is a different version. If Python 3.12 is missing,
install it with `uv python install 3.12`.

## Setup

From a fresh checkout, enter the `PocketAgent` directory and run:

```bash
uv sync
```

This creates `.venv`, installs the package and development tools, and uses
`uv.lock` to reproduce dependency versions. Run project commands through `uv run`
to use this environment. Initial setup needs access to download uncached packages;
running the CLI and checks requires no API key, LLM, GPU, database, or application
service. The package supports macOS and Linux.

Configuration is optional; defaults work immediately. To create local settings:

```bash
cp .env.example .env
```

`Settings` reads `.env` in the current working directory. Environment variables
override that file, which overrides the defaults:

| Variable | Default | Values |
| --- | --- | --- |
| `POCKETAGENT_ENV` | `development` | Any nonempty environment name |
| `POCKETAGENT_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (case insensitive) |

`.env` and local environment variants are ignored by Git. Keep secrets outside
source control; no model credentials are needed for M00. Application logs go to
stderr with a timestamp, severity, logger name, and message.

## CLI

```bash
uv run pocketagent --help
uv run pocketagent version
uv run pocketagent doctor
```

`doctor` reports the Python version, installed package version, and configuration
status. Invalid configuration causes commands to exit with a diagnostic and a
nonzero status.

## Verification

Run the canonical verification sequence:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

To format code during development:

```bash
uv run ruff format .
```

Tests cover package installation, configuration, logging, and the installed CLI
from an isolated directory. Imports resolve through the installed `src` package.

## Troubleshooting local installation

On macOS, if `uv sync` succeeds but the CLI cannot import `pocketagent`, check
`uv run python -v -c 'import pocketagent'`. A `Skipping hidden .pth file` message
means Python is ignoring the editable installation because of a filesystem flag.
Clear the flag on the generated environment files, then retry:

```bash
chflags nohidden .venv/lib/python3.12/site-packages/*.pth
uv run pocketagent doctor
```

If the flags return, move the checkout outside the synchronized folder and run
`uv sync` there. See the [CPython issue](https://github.com/python/cpython/issues/148121)
for details about hidden `.pth` files.
