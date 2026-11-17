"""The hand-edited list of documents to validate (``sks.toml``).

The list looks like this, with paths relative to the folder holding it::

    [[documents]]
    path = "docs/requirements.md"

    [[documents]]
    path = "docs/glossary.md"

Anything else in the file is rejected, so a typo (``[[document]]``, ``paht``)
is reported instead of silently validating nothing.
"""

import tomllib
from pathlib import Path

MANIFEST_NAME = "sks.toml"


class ManifestError(Exception):
    """The document list is missing or malformed."""


def load_manifest(path: Path) -> list[str]:
    """Return the document paths listed in the manifest at ``path``, as written."""
    if not path.is_file():
        raise ManifestError(f"document list not found: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ManifestError(f"{path} is not valid UTF-8 text") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"{path} is not valid TOML: {exc}") from exc

    unknown = sorted(set(data) - {"documents"})
    if unknown:
        raise ManifestError(f"{path}: unknown key(s) {', '.join(unknown)}; only [[documents]] entries are allowed")

    entries = data.get("documents", [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ManifestError(f"{path}: 'documents' must be written as [[documents]] entries")

    paths: list[str] = []
    for number, entry in enumerate(entries, start=1):
        where = f"{path}: [[documents]] entry {number}"
        unknown = sorted(set(entry) - {"path"})
        if unknown:
            raise ManifestError(f"{where}: unknown key(s) {', '.join(unknown)}; only 'path' is allowed")
        document_path = entry.get("path")
        if not isinstance(document_path, str) or not document_path.strip():
            raise ManifestError(f"{where}: 'path' must be a non-empty string")
        if document_path in paths:
            raise ManifestError(f"{where}: '{document_path}' is listed more than once")
        paths.append(document_path)
    return paths
