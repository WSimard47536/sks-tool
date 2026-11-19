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
that starts with a YAML front matter block declaring its type, title and
description:

```markdown
---
type: requirements
title: Data logger requirements
description: What the data logger must do to record flight data.
---

(Markdown body)
```

Every document needs all three keys:

- `type`: one of the types below, in lowercase.
- `title`: at most 5 words.
- `description`: what the document contains, in at most 100 words.

Words are counted as runs of characters separated by spaces. Other front
matter keys are ignored.

The document types are:

| Type | What the document is for |
|---|---|
| `requirements` | What the project must satisfy; if one is not met, the project misses its objectives, does not work, or is unsafe. |
| `specs` | How it is built: diagrams, the design choices made, and why. |
| `overview` | What the project is, what it does and why, with a system diagram. |
| `glossary` | What the project's terms mean. |

Each template (see [Creating a document](#creating-a-document)) starts with a
comment stating what the document is for. The body of `requirements`
documents is defined below; the blocks of the other types are not defined
yet, so their templates hold only the front matter and that comment, and
every body is accepted.

### Requirements documents

A `requirements` document is a sequence of requirements and nothing else:
outside them, only blank lines and `<!-- comments -->` are allowed. Each
requirement is written as:

```markdown
## LOG-001

The logger **shall** sample each accelerometer axis at 1 kHz.

- Rationale: Vibration analysis needs content up to 400 Hz, which requires sampling above 800 Hz.
```

- **ID**: the level-2 heading. It must be unique across every document listed
  in `sks.toml`; there are no other naming rules yet.
- **Statement**: the paragraph right under the heading, required. It must be a
  single sentence on one line, ending with `.` (no `.`, `!` or `?` followed
  by a space before that, so write abbreviations such as "e.g." in full). It
  contains the word **shall** exactly once, in bold and lowercase
  (`**shall**`), and is at most 100 characters long as rendered (the `**`
  do not count). It states what the system must do, never what it must not:
  "shall not" is rejected, so reword it positively ("shall write each log to
  a new file" rather than "shall not overwrite a log file").
- **Fields**: a bullet list after the statement, one field per line as
  `- <Field>: <value>`. The only field for now is `Rationale`: optional, why
  the requirement exists, at most 200 characters, and not empty when present.

Comments may span several lines but must take whole lines. A document must
contain at least one requirement. The `requirements` template holds five
example requirements for a fictional data logger; replace them with your own,
since their IDs clash with any other document made from the template.

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
