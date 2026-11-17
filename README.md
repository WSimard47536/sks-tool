# SKS Tool

Templates and validators for Structured Knowledge Standard (SKS) documents.

## Contents

- [Setup](#setup)
- [Developing](#developing)
- [Tooling](#tooling)
- [Usage](#usage)

## Setup

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

## Developing

Day to day:

```bash
uv run ruff check . --fix  # lint
uv run ruff format .       # format
uv run mypy .              # type check
uv run pytest              # tests
```

`pre-commit` runs the same checks (plus `gitleaks` secret scanning) on every
`git commit`; CI reruns them on `ubuntu-latest`, `windows-latest`, and
`macos-latest`, and separately runs `pip-audit` against the dependency tree.

### Where new code goes

Library code goes under `src/sks_tool/`; new CLI commands are
`@app.command()` functions added to `src/sks_tool/cli.py` (see
`types` there for the pattern). Tests go in `tests/`, one `test_<module>.py`
per module.

### Adding dependencies

`uv add <package>` for a runtime dependency, `uv add --dev <package>` for a
dev-only one (or edit `pyproject.toml` directly), then `uv sync`. Commit the
updated `uv.lock` — the `uv-lock` pre-commit hook checks it's in sync with
`pyproject.toml` and fails the commit if you forget.

### Tweaking config

- **Lint/format rules** — `[tool.ruff]` / `[tool.ruff.lint]` in
  `pyproject.toml`. `select = [...]` controls which rule sets run; see the
  [ruff rule list](https://docs.astral.sh/ruff/rules/) for codes to add, or
  add a `[tool.ruff.lint.per-file-ignores]` table for exceptions.
- **Type checking** — `[tool.mypy]` in `pyproject.toml`, currently `strict =
  true`. Relax it for a specific import with a `[[tool.mypy.overrides]]`
  table (useful for dependencies without type stubs).
- **Test config** — `[tool.pytest.ini_options]` in `pyproject.toml`
  (`testpaths`, coverage via `--cov`).
- **pre-commit hooks** — `.pre-commit-config.yaml`. Add, remove, or
  reconfigure hooks there; re-run `uv run pre-commit install` if you change
  which hooks run at all (already done once by `init.py`).
- **CI** — `.github/workflows/ci.yml`. Mirrors the day-to-day commands above
  across Linux, Windows, and macOS — update it if those commands change.
- **Docs site** — `mkdocs.yml` (nav, theme) and `docs/*.md` (content).
  Preview locally with `uv run mkdocs serve`.

### Releasing

Add an entry to `CHANGELOG.md` as part of the PR that ships a notable change.

Also bump the version in `pyproject.toml`.

Bumping the version changes `uv.lock` too (it embeds the project's own
version) — run `uv sync` and stage the updated `uv.lock` alongside
`pyproject.toml`.

## Tooling

This section explains what each tool/file in this project is for and why
it's here, so it's less of a mystery the first time you touch it.

- **[`uv`](https://docs.astral.sh/uv/)** — installs dependencies and manages
  the virtual environment (`.venv/`, created for you, never committed).
  `uv.lock` records the exact version of every dependency that was
  installed; it's committed so everyone (and CI) gets the identical set.
  Don't hand-edit `uv.lock` — it's regenerated automatically by `uv sync`
  whenever `pyproject.toml`'s dependencies change.
- **[`ruff`](https://docs.astral.sh/ruff/)** — lints and formats the code
  (one tool doing what `flake8` + `black` + `isort` used to do separately).
  Configured under `[tool.ruff]` in `pyproject.toml`.
- **[`mypy`](https://mypy-lang.org/)** — checks that type hints are
  consistent, catching a class of bugs before you ever run the code.
  Configured in strict mode under `[tool.mypy]` in `pyproject.toml`.
- **[`pytest`](https://docs.pytest.org/)** — runs the tests in `tests/`
  (or each package's own `tests/`, for the workspace layout).
- **[`pre-commit`](https://pre-commit.com/)** — runs the checks below
  automatically on every `git commit`, so problems are caught on your
  machine instead of in CI or in review. Configured in
  `.pre-commit-config.yaml`; installed once via `uv run pre-commit install`
  (done for you automatically by `init.py`).
- **[`gitleaks`](https://github.com/gitleaks/gitleaks)** (via `pre-commit`)
  — scans every commit for things that look like secrets (API keys,
  tokens, credentials) before they leave your machine.
- **`.github/workflows/ci.yml`** — re-runs `ruff`
  and `mypy`
  and the test suite on every push and pull request, on Linux, Windows,
  *and* macOS (bugs that only show up on one OS are a real and recurring
  problem — this is here to catch them before they ship). A separate job
  runs [`pip-audit`](https://pypi.org/project/pip-audit/), which checks
  every dependency against known security vulnerabilities.
- **`CHANGELOG.md`** — a running, human-readable log of notable changes;
  update it as part of the PR that makes the change.
- **`mkdocs.yml` / `docs/`** — a documentation site scaffold. Preview it
  locally with `uv run mkdocs serve`.

## Usage

SKS is the Structured Knowledge Standard. An SKS document is a Markdown file
that starts with a YAML front matter block declaring its type:

```markdown
---
type: requirements
---

(Markdown body)
```

The document types are:

| Type | What the document is for |
|---|---|
| `requirements` | What the project must satisfy; if one is not met, the project misses its objectives, does not work, or is unsafe. |
| `specs` | How it is built: diagrams, the design choices made, and why. |
| `overview` | What the project is, what it does and why, with a system diagram. |
| `glossary` | What the project's terms mean. |

Their blocks are not defined yet, so each template holds only the `type` and
a comment stating what the document is for, and the parsers accept any body.

### Using it from another repository

`sks-tool` is meant to be added to a technical repository as a git submodule
and run from that repository's root. The host repository does not need to be
a Python project; it only needs [`uv`](https://docs.astral.sh/uv/) installed.

```bash
git submodule add <sks-tool repository URL> tools/sks-tool
uv run --project tools/sks-tool sks-tool validate
```

`--project` tells `uv` where the tool lives; the working directory stays the
host repository, so `sks.toml` and the documents it lists belong to the host
repository, not to the submodule. The commands below are written as run from
inside this repository; from a host repository, put `--project tools/sks-tool`
after `uv run`.

### Creating a document

```bash
uv run sks-tool types                              # list the document types
uv run sks-tool new requirements docs/reqs.md      # create one from its template
```

`new` refuses to overwrite an existing file.

### Validating documents

The documents to validate are listed by hand in `sks.toml`, in the folder you
run the tool from. Paths are relative to that file:

```toml
[[documents]]
path = "docs/reqs.md"

[[documents]]
path = "docs/glossary.md"
```

```bash
uv run sks-tool validate                           # human-readable report
uv run sks-tool validate --json                    # the same results as JSON
uv run sks-tool validate --config path/to/sks.toml
```

Each issue is printed as `path:line: message [code]`. The exit code is `0`
when every document is valid, `1` when any document has an issue, and `2`
when `sks.toml` is missing or malformed.

### How validation is organised

- `src/sks_tool/parsers/common.py` is the main parser. It reads the file,
  checks that it declares a known `type`, runs the checks shared by every
  document type (`validate_common`, empty for now), then hands the document
  to the parser for its type.
- `src/sks_tool/parsers/<type>.py` holds the checks for one document type
  (empty for now).
- `src/sks_tool/templates/<type>.md` is the template `new` copies. A test
  checks that every template passes its own parser, so the two cannot drift
  apart.
- `src/sks_tool/doctypes.py` registers the types and holds the one-line
  summary of each, shown by `sks-tool types` and repeated as a comment in the
  template.

To add a document type, add its parser and template and register it in
`src/sks_tool/doctypes.py`.
