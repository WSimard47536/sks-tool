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
