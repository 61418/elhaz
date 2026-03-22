# Contributing to elhaz

Thank you for your interest in contributing. This document covers everything you need to get set up, understand the codebase, and submit a pull request.

## Table of contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Project structure](#project-structure)
- [Architecture overview](#architecture-overview)
- [Development workflow](#development-workflow)
- [Coding standards](#coding-standards)
- [Adding or removing dependencies](#adding-or-removing-dependencies)
- [Pull request process](#pull-request-process)
- [Release process](#release-process)
- [License](#license)

---

## Prerequisites

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) — used for all project management (virtualenv, dependencies, running tools)
- An AWS account with credentials available in your environment for any tests that exercise session initialization

Install `uv` if you do not already have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Setup

```bash
git clone https://github.com/michaelthomasletts/elhaz.git
cd elhaz

# Create the virtualenv and install all dependencies including dev extras
uv sync --all-groups

# Activate the virtualenv (required for pre-commit and direct tool invocation)
source .venv/bin/activate

# Install pre-commit hooks
uv run pre-commit install
```

After this, `ruff`, `pytest`, and all other dev tools are available via `uv run <tool>` or directly inside the activated virtualenv.

---

## Project structure

```
elhaz/
├── cli/
│   ├── __main__.py     # Entry point; wires typer app
│   ├── config.py       # CLI commands for config management
│   ├── daemon.py       # CLI commands for daemon control
│   ├── output.py       # Output formatting utilities
│   └── prompts.py      # Interactive questionary prompts
├── config.py           # Config CRUD: read/write/validate YAML configs
├── constants.py        # Global constants (paths, limits); singleton `state`
├── daemon.py           # UNIX socket server (Server), client (Client), and
│                       # business logic (DaemonService)
├── exceptions.py       # Custom exception hierarchy
├── models.py           # Pydantic models for configs and the daemon protocol
└── session.py          # Session and SessionCache
tests/
.github/
├── workflows/
│   ├── push.yml                # CI/CD for pushes to main
│   ├── pull_request.yml        # CI for pull requests
│   └── validate_pr_title.yml   # Enforce conventional commit PR titles
pyproject.toml
.pre-commit-config.yaml
```

**Module dependency order** (from least to most dependent):

```
exceptions → constants → models → config → session → daemon → cli
```

Do not introduce imports that create cycles within this order.

---

## Architecture overview

### Daemon

The daemon is a long-running UNIX domain socket server (`~/.elhaz/sock/daemon.sock`) that manages a bounded, LRU in-memory cache of refreshable AWS sessions. It is designed around a clean separation of concerns:

- **`DaemonService`** — pure business logic. Owns the `SessionCache`, implements all protocol actions (`add`, `credentials`, `list`, `remove`, `whoami`), and has no awareness of sockets or transport.
- **`Server`** — transport layer. Accepts connections, spawns a thread per connection, reads one newline-delimited JSON request, writes one JSON response, and delegates all logic to `DaemonService`.
- **`Client`** — short-lived context manager for sending a single request. Used by the CLI to communicate with a running daemon.

Each request/response is a newline-delimited JSON envelope validated by `RequestModel` / `ResponseModel`. The protocol is versioned (`version: 1`) to allow future evolution without breaking existing clients.

### Session refresh

Sessions are backed by [`boto3-refresh-session`](https://github.com/61418/boto3-refresh-session). Credential refresh is handled transparently by `STSRefreshableSession` — the daemon does not manage a refresh loop manually.

### Config files

Configs live in `~/.elhaz/configs/<name>.yaml`. Each config is a YAML serialization of `ConfigModel` and is validated with Pydantic on every read and write. File-level exclusive locks (`fcntl` on POSIX, `msvcrt` on Windows) prevent concurrent writes.

### Socket lifecycle

Key invariants the `Server` enforces:

- A stale socket file (no listener) is detected and removed before binding.
- A live socket (listener responds) raises `ElhazDaemonError` rather than overwriting it.
- The socket file is always unlinked on shutdown, whether via `SIGTERM`, `SIGINT`, or `atexit`.

When writing tests that start a `Server`, always use a temporary socket path via `tmp_path` so tests do not interfere with each other or a live daemon.

---

## Development workflow

### Running tests

```bash
uv run pytest tests/ -v
```

Log output is enabled at INFO level by default (see `[tool.pytest.ini_options]` in `pyproject.toml`).

### Linting and formatting

```bash
# Check formatting
uv run ruff format --check .

# Apply formatting
uv run ruff format .

# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .
```

Ruff is configured with `line-length = 79`, targeting Python 3.10, and enforces `E`, `F`, `W`, and `I` (isort) rules. See `[tool.ruff]` in `pyproject.toml` for the full configuration.

### Pre-commit

Pre-commit runs `ruff`, `ruff format --check`, and `pytest` automatically before every commit. If any hook fails, the commit is aborted. Fix the reported issues and re-stage before retrying.

To run all hooks manually without committing:

```bash
uv run pre-commit run --all-files
```

---

## Coding standards

- **Python 3.10+.** Use `match`/`case`, `X | Y` union syntax, and `X | None` instead of `Optional[X]` in new code.
- **Typing is mandatory.** All public functions and methods must have complete type annotations. Return types are not optional.
- **Docstrings use numpydoc format.** Public classes and functions require a summary line, a `Parameters` section, and a `Returns` or `Raises` section where applicable. Private helpers do not require docstrings but should have one if the logic is non-obvious.
- **Pydantic for protocol and config validation.** Use `_BaseModel` (which sets `extra="forbid"`) as the base for all new models in `models.py`.
- **Do not add dependencies without discussion.** The standard library is preferred. New third-party dependencies require a clear justification and must be added to `pyproject.toml` via `uv add`.
- **MPL-2.0 license header.** Every new `.py` file must begin with:

  ```python
  # This Source Code Form is subject to the terms of the Mozilla Public
  # License, v. 2.0. If a copy of the MPL was not distributed with this
  # file, You can obtain one at https://mozilla.org/MPL/2.0/.
  ```

- **No unnecessary abstraction.** Prefer direct, explicit code over clever generalization. Three similar lines are better than a premature helper.

---

## Adding or removing dependencies

```bash
# Add a runtime dependency
uv add <package>

# Add a dev-only dependency
uv add --group dev <package>

# Remove a dependency
uv remove <package>
```

`uv` updates both `pyproject.toml` and `uv.lock` automatically. Commit both files together.

---

## Pull request process

1. **Branch from `main`.**
2. **Keep changes focused.** One logical change per PR. If you find yourself editing unrelated code, open a separate PR.
3. **Write tests** for every meaningful behavioral change.
4. **PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/).** This is enforced automatically by `validate_pr_title.yml`. Accepted types:

   | Type | When to use |
   |---|---|
   | `feat` | New user-facing feature |
   | `fix` | Bug fix |
   | `perf` | Performance improvement |
   | `refactor` | Code change with no behavior change |
   | `docs` | Documentation only |
   | `style` | Formatting, whitespace |
   | `test` | Adding or fixing tests |
   | `build` | Build system or dependency changes |
   | `ci` | CI/CD workflow changes |
   | `chore` | Maintenance tasks |
   | `revert` | Reverts a prior commit |

   Breaking changes are indicated with a `!` suffix: `feat!: remove legacy config format`.

5. **Squash merge only.** The PR title becomes the commit message on `main`, which release-please uses to determine the next version. Do not merge with a merge commit or rebase.

6. To **skip the release and publish pipeline** for a given PR, append `[skip release]` to the PR title before merging:

   ```
   chore: update README [skip release]
   ```

---

## Release process

Releases are fully automated via [release-please](https://github.com/googleapis/release-please).

1. When a PR is merged to `main`, release-please inspects the commit message and opens or updates a release PR with a version bump and changelog entry.
2. When the release PR is merged, release-please creates a GitHub release and tags the commit.
3. The `push.yml` workflow then builds the package and publishes it to **TestPyPI** first, then to **PyPI** — in sequence, using OIDC Trusted Publishing. Publication to PyPI only proceeds if TestPyPI succeeds.

**To target a specific version** (e.g., for an alpha or beta release), include a `Release-As:` footer in your commit body before squash-merging. Use PEP 440 version strings, not semver, since PyPI rejects semver pre-release identifiers:

```
feat: initial public alpha

Release-As: 1.0.0a1
```

Valid PEP 440 pre-release identifiers: `aN` (alpha), `bN` (beta), `rcN` (release candidate).

---

## License

By contributing to elhaz, you agree that your contributions will be licensed under the [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).
