# Contributing to bml-connect-python

Thank you for taking the time to contribute! This document covers everything you need to get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Quality](#code-quality)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

---

## Code of Conduct

Be respectful. Constructive feedback is welcome; personal attacks are not. Issues and pull requests that are abusive or off-topic will be closed.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/bml-connect-python.git
   cd bml-connect-python
   ```
3. Add the upstream remote so you can pull future changes:
   ```bash
   git remote add upstream https://github.com/quillfires/bml-connect-python.git
   ```

---

## Development Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management. Make sure you have it installed before continuing.

```bash
# Install all dependencies including dev tools
poetry install

# Activate the virtual environment
poetry shell
```

Requirements:
- Python 3.9 or higher
- Poetry 1.2 or higher

---

## Making Changes

Always create a feature branch from `main`. Never commit directly to `main`.

```bash
git checkout main
git pull upstream main
git checkout -b your-branch-name
```

Branch naming conventions:

| Type | Pattern | Example |
|---|---|---|
| Bug fix | `fix/short-description` | `fix/async-session-init` |
| New feature | `feat/short-description` | `feat/cancel-transaction` |
| Documentation | `docs/short-description` | `docs/webhook-examples` |
| Refactor | `refactor/short-description` | `refactor/error-handling` |

---

## Code Quality

All code must pass the following checks before a pull request will be reviewed. Run them in this order:

```bash
# Sort imports
poetry run isort src/ tests/

# Format code
poetry run black src/ tests/

# Type checking
poetry run mypy src/

# Lint
poetry run flake8 src/ tests/
```

You can run all four in one go:

```bash
poetry run isort src/ tests/ && \
poetry run black src/ tests/ && \
poetry run mypy src/ && \
poetry run flake8 src/ tests/
```

**Standards enforced:**

- All public functions and methods must have type annotations
- No `f"string"` where a plain string will do
- No bare `assert` statements outside of tests — use `if/raise` for runtime guards
- Line length: 88 characters (Black default)

---

## Running Tests

```bash
poetry run pytest
```

For verbose output:

```bash
poetry run pytest -v
```

For a specific test file:

```bash
poetry run pytest tests/test_client.py -v
```

**When to add tests:**

- Every bug fix should include a test that would have caught the bug
- Every new feature or method must have at least one test covering the happy path and one covering an error case
- Tests for async methods must use `pytest-asyncio`

---

## Submitting a Pull Request

1. Make sure all quality checks and tests pass locally
2. Push your branch to your fork:
   ```bash
   git push origin your-branch-name
   ```
3. Open a pull request against the `main` branch of this repo
4. Fill in the PR description — what changed, why, and how to test it
5. Link any related issues using `Closes #issue-number` in the description

**PR checklist:**

- [ ] `isort`, `black`, `mypy`, and `flake8` all pass
- [ ] Tests added or updated for the change
- [ ] `CHANGELOG.md` updated under an `[Unreleased]` section
- [ ] No new dependencies added without discussion in an issue first

Pull requests that fail the CI checks will not be reviewed until they pass.

---

## Reporting Bugs

Open an issue at [github.com/quillfires/bml-connect-python/issues](https://github.com/quillfires/bml-connect-python/issues) and include:

- Python version (`python --version`)
- SDK version (`pip show bml-connect-python`)
- Minimal code that reproduces the issue
- The full error traceback
- What you expected to happen vs what actually happened

**Security issues** — do not open a public issue. Email fayaz.quill@gmail.com directly.

---

## Requesting Features

Open an issue and describe:

- What you want to do that you currently can't
- The use case behind it (what problem it solves)
- Any API behaviour from the [official BML Connect docs](https://github.com/bankofmaldives/bml-connect) that's relevant

Feature requests that align with the official BML Connect API surface are prioritised. Features that diverge significantly from the API spec will be considered on a case-by-case basis.

---

Made with ❤️ for the Maldivian developer community
