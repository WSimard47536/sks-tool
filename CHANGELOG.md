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
