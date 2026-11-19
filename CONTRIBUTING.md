# Contributing to SKS Tool

This guide is for developing `sks-tool`. To use it, see the
[README](README.md).

## Contents

- [Setup](#setup)
- [Developing](#developing)
- [How validation is organised](#how-validation-is-organised)
- [Tooling](#tooling)

## Setup

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

From inside this repository the tool runs as `uv run sks-tool …`, without the
`--project` option the README uses from a host repository.

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
  which hooks run at all.
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

## How validation is organised

`src/sks_tool/pipeline.py` runs the steps for one document, in order:

1. `document.py` splits the file into front matter and body.
2. `parsers/base.py`: `CommonParser` reads the document's `type`.
3. `validators/base.py`: `CommonValidator` runs the checks shared by every
   type.
4. `parsers/<type>/parser.py` reads the body into the structure defined in
   `docs/<type>/doc.py`.
5. `validators/<type>/validator.py` checks that structure.

Steps 1, 2 and 4 report `ParserFinding`s; steps 3 and 5 report `ValidatorFinding`s
(`src/sks_tool/findings.py`). Parsers implement the `Parser` interface and
validators the `Validator` interface, both in their package's `base.py`.
`docs/`, `parsers/` and `validators/` follow the same layout: one package per
document type, with one subpackage per block once a type's blocks are
defined. For now no blocks are defined and no checks exist beyond the front
matter.

- `src/sks_tool/templates/<type>.md` is the template `new` copies. A test
  checks that every template passes its own parser and validator, so they
  cannot drift apart.
- `src/sks_tool/doctypes.py` registers the types: each one's summary (shown
  by `sks-tool types` and repeated as a comment in the template), parser and
  validator. The type checker rejects a type whose parser produces a
  structure its validator does not check.

To add a document type, add its `docs/`, `parsers/` and `validators/`
packages and its template, and register it in `src/sks_tool/doctypes.py`.

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
- **[`pytest`](https://docs.pytest.org/)** — runs the tests in `tests/`.
- **[`pre-commit`](https://pre-commit.com/)** — runs the checks below
  automatically on every `git commit`, so problems are caught on your
  machine instead of in CI or in review. Configured in
  `.pre-commit-config.yaml`; installed once via `uv run pre-commit install`
  (see [Setup](#setup)).
- **[`gitleaks`](https://github.com/gitleaks/gitleaks)** (via `pre-commit`)
  — scans every commit for things that look like secrets (API keys,
  tokens, credentials) before they leave your machine.
- **`.github/workflows/ci.yml`** — on every push and pull request, re-runs
  `ruff check`, `ruff format --check`, `mypy`, the test suite and
  `mkdocs build --strict`, on Linux, Windows, *and* macOS (bugs that only
  show up on one OS are a real and recurring problem — this is here to
  catch them before they ship). A separate job runs
  [`pip-audit`](https://pypi.org/project/pip-audit/), which checks every
  dependency against known security vulnerabilities.
- **`CHANGELOG.md`** — a running, human-readable log of notable changes;
  update it as part of the PR that makes the change.
- **`mkdocs.yml` / `docs/`** — a documentation site scaffold. Preview it
  locally with `uv run mkdocs serve`.
