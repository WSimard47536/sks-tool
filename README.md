# SKS Tool

Templates and validators for Structured Knowledge Standard (SKS) documents.

This guide is for using `sks-tool`. To work on `sks-tool` itself, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Contents

- [SKS documents](#sks-documents)
- [Installing](#installing)
- [Creating a document](#creating-a-document)
- [Validating documents](#validating-documents)

## SKS documents

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
a comment stating what the document is for, and every body is accepted.

## Installing

`sks-tool` is meant to be added to a technical repository as a git submodule
and run from that repository's root. The host repository does not need to be
a Python project; it only needs [`uv`](https://docs.astral.sh/uv/) installed.

```bash
git submodule add <sks-tool repository URL> tools/sks-tool
uv run --project tools/sks-tool sks-tool --help
```

`--project` tells `uv` where the tool lives; the working directory stays the
host repository, so `sks.toml` and the documents it lists belong to the host
repository, not to the submodule. The commands below assume the submodule is
at `tools/sks-tool`; adjust the path if you put it elsewhere.

## Creating a document

```bash
uv run --project tools/sks-tool sks-tool types                          # list the document types
uv run --project tools/sks-tool sks-tool new requirements docs/reqs.md  # create one from its template
```

`new` refuses to overwrite an existing file.

## Validating documents

The documents to validate are listed by hand in `sks.toml`, in the folder you
run the tool from. Paths are relative to that file:

```toml
[[documents]]
path = "docs/reqs.md"

[[documents]]
path = "docs/glossary.md"
```

```bash
uv run --project tools/sks-tool sks-tool validate                           # human-readable report
uv run --project tools/sks-tool sks-tool validate --json                    # the same results as JSON
uv run --project tools/sks-tool sks-tool validate --config path/to/sks.toml
```

Each document is first **parsed** (read into its structure), then
**validated** (checked against the rules). Every finding says which of the two
found it, what is wrong, and how to fix it:

```text
docs/reqs.md:1: parse: the file does not start with a front matter block [front-matter-missing]
    fix: make the first line '---', then 'type: <type>', then a closing '---'
docs/reqs.md: type-specific validation skipped until the parse findings are fixed
```

A validation finding also names where in the document the problem is, for
example `docs/reqs.md:7: validate: requirement REQ-012 › rationale: is empty
[rationale-empty]`. The checks shared by every type run as soon as the file
is read; the checks for its type run only once it is fully parsed, and a
document that is not fully parsed is reported as skipped rather than ok. Output
is always UTF-8, so any path or message prints, even when redirected to a file
or a CI log.

With `--json`, each document has `ok`, `validated` and a `findings` list;
every finding has the keys `kind` (`parse` or `validate`), `code`, `message`,
`hint`, `line` and `location`, set to `null` when they do not apply.

The exit code is `0` when every document is valid, `1` when any document has
a finding, and `2` when `sks.toml` is missing or malformed.
