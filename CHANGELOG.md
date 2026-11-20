# Changelog

All notable changes to `sks-tool` are documented here. This project
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

- Initial scaffold generated from the org Python project template.
- Document types `requirements`, `specs`, `overview` and `glossary`, each
  with an empty template and its own parser.
- `sks-tool new` creates a document from a template, `sks-tool validate`
  checks the documents listed in `sks.toml` (with `--json` output), and
  `sks-tool types` lists the document types.
- Removed the placeholder `hello` command.
- Each document type has a summary of what the document is for, shown by
  `sks-tool types` and as a guidance comment in its template.
- Documented running the tool from a host repository as a git submodule.
- Split checking into parsing and validation. `sks_tool.parsers` reads each
  document into its structure (`sks_tool.docs`) and `sks_tool.validators`
  checks it, each with a `base.py` holding its interface and the part shared
  by every type, and one package per document type.
- Replaced `Issue` with `ParserFinding` and `ValidatorFinding`. Every finding
  now has a `hint` saying how to fix it, and the output labels each one
  `parse` or `validate`. The checks shared by every type run as soon as the
  file is read; for a document that cannot be fully parsed, the checks for
  its type are reported as skipped.
- Changed the `validate --json` output: each document's `issues` list is now
  `findings`, and documents have a `validated` key.
- `sks-tool` always writes UTF-8, so a path or message the system code page
  cannot encode no longer crashes it when its output is redirected.
- Split the README into a user guide (`README.md`) and a guide for developing
  `sks-tool` (`CONTRIBUTING.md`).
- Every document's front matter now needs a `title` (at most 5 words) and a
  `description` (at most 100 words) besides its `type`; every template has
  them.
- Defined `requirements` documents: a sequence of requirements, each an ID
  heading, a one-sentence statement with a bold **shall**, and an optional
  rationale. The template holds five example requirements.
- `validate` checks that requirement IDs are unique across every document in
  `sks.toml`.
- Requirement statements must be positive: "shall not" is reported as
  `statement-negative`.
- Defined `glossary` documents: a sequence of terms in alphabetical order,
  each a term heading of at most 100 characters and a one-line definition of
  at most 200. Terms are unique across every glossary in `sks.toml`, ignoring
  case. The template holds four example terms.
- Every requirement now states its type on the first line under its ID:
  `Type: Business`, `Type: Functional` or `Type: Non-functional`, followed
  by a blank line. The template shows each type.
- Defined `overview` documents: a Summary and a Purpose of at most 200
  characters each, then a System diagram shown from an editable `.drawio.svg`
  file. `new overview` also creates a blank `system_diagram.drawio.svg`.
- Defined `specs` documents: design decisions written like requirements,
  with a `Functional` or `Non-functional` type, a statement of at most 200
  characters, a required rationale and an optional diagram named after the
  spec's ID. `new specs` also creates the example spec's blank diagram.
- Requirements and specs now have a `Status:` line (`Pending`, `Unfulfilled`,
  `Underway` or `Fulfilled`) and an `Acceptance criteria:` checkbox list that
  must agree with the status.
- Requirement and spec IDs are unique together; the duplicate finding is now
  `id-duplicate` (was `requirement-id-duplicate`).
- Requirement and spec IDs may not contain whitespace or parentheses
  (`id-invalid`), and a blank line is required before the acceptance
  criteria and before a spec's diagram, so each renders as its own paragraph.
