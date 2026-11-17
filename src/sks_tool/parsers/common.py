"""The main parser: checks shared by every document type, then dispatch.

``validate_file`` is the single entry point for validating a document. It
reads the file, runs the common checks in ``validate_common``, and then runs
the parser for the document's own type.

No common sections are defined yet, so the only common check is that the
document declares a known ``type``. Add checks shared by every document type
to ``validate_common``.
"""

from dataclasses import dataclass
from pathlib import Path

from sks_tool.doctypes import DOC_TYPES, DocType
from sks_tool.document import Document, Issue, load_document


@dataclass(frozen=True)
class Result:
    """The outcome of validating one document."""

    doc_type: str | None
    """The document's type, or ``None`` if it could not be determined."""
    issues: list[Issue]

    @property
    def ok(self) -> bool:
        return not self.issues


def resolve_type(document: Document) -> tuple[DocType | None, list[Issue]]:
    """Find the document's type from the ``type`` key of its front matter."""
    if "type" not in document.front_matter:
        return None, [Issue("type-missing", "front matter must have a 'type' key")]
    declared = document.front_matter["type"]
    known = ", ".join(DOC_TYPES)
    if not isinstance(declared, str):
        return None, [Issue("type-not-text", f"'type' must be one of: {known}")]
    doc_type = DOC_TYPES.get(declared)
    if doc_type is None:
        return None, [Issue("type-unknown", f"unknown type '{declared}'; expected one of: {known}")]
    return doc_type, []


def validate_common(document: Document) -> list[Issue]:
    """Return the problems found by the checks shared by every document type."""
    return []


def validate_file(path: Path) -> Result:
    """Validate the document at ``path``."""
    document, issues = load_document(path)
    if document is None:
        return Result(doc_type=None, issues=issues)

    doc_type, issues = resolve_type(document)
    issues += validate_common(document)
    if doc_type is None:
        return Result(doc_type=None, issues=issues)

    issues += doc_type.validate(document)
    return Result(doc_type=doc_type.name, issues=issues)
