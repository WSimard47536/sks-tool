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
comment stating what the document is for, then example content for a
fictional flight data logger; replace it with your own. The body of each type
is defined below.

### Requirements and specs documents

A `requirements` document is a sequence of requirements, and a `specs`
document a sequence of specs, and nothing else: outside them, only blank
lines and `<!-- comments -->` are allowed. A requirement says what the system
must do; a spec records a design decision, "we do it this way, and this is
why", the kind of information that would not go in the code's own
documentation. Both are written the same way:

```markdown
## LOG-004

Type: Functional

Status: Underway

The logger **shall** close the current log file within 50 ms of a power-loss signal.

- Rationale: The hold-up capacitor keeps the logger powered for 80 ms after power loss.

Acceptance criteria:

- [x] The bench test closes the file within 50 ms in 100 out of 100 power cuts.
- [ ] The flight test log shows no truncated file after a power loss.
```

In this order:

- **ID**: the level-2 heading, with no whitespace or parentheses (it names
  files and links). It must be unique across every requirement and spec
  listed in `sks.toml`, together; there are no other naming rules yet.
- **Type**: the first line under the heading, required, written exactly as
  `Type: <type>` and followed by a blank line, with one of:
  - `Business` (requirements only): what the system must do to fulfil its
    purpose;
  - `Functional`: what it must do to fulfil the business requirements;
  - `Non-functional`: how it must do it, such as safety standards or
    performance.
- **Status**: the next line, required, written exactly as `Status: <status>`
  and followed by a blank line, with one of `Pending` (work has not started),
  `Unfulfilled` (the current implementation is not satisfactory), `Underway`
  or `Fulfilled`.
- **Statement**: the next paragraph, required: a single sentence on one line,
  ending with `.` (no `.`, `!` or `?` followed by a space before that, so
  write abbreviations such as "e.g." in full).
- **Fields**: a bullet list after the statement, one field per line as
  `- <Field>: <value>`. The only field for now is `Rationale`, at most 200
  characters and not empty when present.
- **Acceptance criteria**: required: after a blank line, the line
  `Acceptance criteria:`, then a
  checkbox list with at least one criterion, one per line, at most 200
  characters: `- [ ] <criterion>`, or `- [x] <criterion>` once it is met. The
  checkboxes must agree with the status: `Fulfilled` needs every box checked,
  any other status at least one unchecked, and `Pending` none checked.

Requirements and specs differ in a few rules:

| | Requirement | Spec |
|---|---|---|
| Type | `Business`, `Functional` or `Non-functional` | `Functional` or `Non-functional` |
| Statement | at most 100 characters as rendered (the `**` do not count); contains **shall** exactly once, in bold and lowercase (`**shall**`); never "shall not", so reword it positively ("shall write each log to a new file" rather than "shall not overwrite a log file") | at most 200 characters; no rule about "shall" |
| Rationale | optional | required |
| Diagram | none | optional, last, after a blank line: one image named after the spec's ID, `![<alt text>](<ID>.drawio.svg)` |

A spec's diagram follows the same rules as an overview's system diagram (see
[Overview documents](#overview-documents)), and its file must be named
`<ID>.drawio.svg`, in any folder relative to the document.

Comments may span several lines but must take whole lines. A document must
contain at least one requirement or spec. The templates' example IDs clash
with any other document made from the same template, so replace them.

The checkboxes render as checkboxes on GitHub and in VS Code's Markdown
preview; a mkdocs site needs the `pymdownx.tasklist` extension of
[PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/extensions/tasklist/)
(installed with mkdocs Material) enabled in its `mkdocs.yml`.

### Glossary documents

A `glossary` document is a sequence of terms and nothing else: outside them,
only blank lines and `<!-- comments -->` are allowed, as in requirements
documents. Each term is written as:

```markdown
## Log file

A file on the logger's non-volatile memory holding the samples of one power-on session.
```

- **Term**: the level-2 heading, a word or a short expression of at most 100
  characters. It must be unique across every glossary listed in `sks.toml`,
  ignoring case ("Log file" and "log file" clash).
- **Definition**: the paragraph right under the term, required: what the term
  means in the project, on one line, at most 200 characters. Nothing else
  follows it.

The terms of a glossary must be in alphabetical order, ignoring case. The
order compares characters as written, so a space sorts before letters ("Log
file" before "Logger"). A document must contain at least one term. The
`glossary` template holds four example terms for the same fictional data
logger; replace them with your own.

### Overview documents

An `overview` document has exactly three sections, in this order, and
nothing else (outside them, only blank lines and `<!-- comments -->`):

```markdown
## Summary

A flight data logger that records the aircraft's sensor data to non-volatile memory.

## Purpose

To give the airframe team the vibration data it needs to confirm the structure stays within its limits.

## System diagram

![System diagram](system_diagram.drawio.svg)
```

- **Summary**: what the system is, in one paragraph on one line, at most 200
  characters.
- **Purpose**: why it is built, with the same limits.
- **System diagram**: a single Markdown image on its own line, pointing to a
  `.drawio.svg` file by a path relative to the document's folder. The file
  must exist and carry an editable draw.io diagram.

A `.drawio.svg` file is both the editable diagram and the image the page
shows, so there is no separate export to keep up to date. Edit it with the
[Draw.io Integration](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio)
extension for VS Code, or with draw.io itself; a plain SVG renamed to
`.drawio.svg` is rejected, since it cannot be edited as a diagram.

A project may have several overviews, for example one per subsystem, each in
its own folder.

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

`new overview` also creates a blank `system_diagram.drawio.svg` next to the
document, for its system diagram, and `new specs` a blank `LOG-S-001.drawio.svg`
for the diagram of its first example spec. `new` refuses to overwrite an existing
file, and writes nothing if any of the files it would create already exists.

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
