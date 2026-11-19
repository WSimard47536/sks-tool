"""The ``Parser`` interface, and the root parser shared by every document.

A parser reads a ``Document`` into a structure. It returns the structure, or
``None`` plus at least one finding saying why it could not; returning ``None``
without a finding is a bug in the parser, and the pipeline stops on it.

``CommonParser`` reads the part shared by every document: the ``type`` key of
its front matter, which selects the parser and validator for the rest.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from sks_tool.document import Document
from sks_tool.findings import ParserFinding

if TYPE_CHECKING:
    # Imported for type checking only: the registry imports every type's
    # parser, so a runtime import here could create an import cycle.
    from sks_tool.doctypes import DocType


class Parser[T](Protocol):
    """Reads a ``Document`` into a structure of type ``T``."""

    def parse(self, document: Document) -> tuple[T | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        ...


class CommonParser:
    """Reads the document's ``type`` and finds it in the registry of document types."""

    def __init__(self, doc_types: Mapping[str, "DocType[Any]"]) -> None:
        self._doc_types = doc_types

    def parse(self, document: Document) -> tuple["DocType[Any] | None", list[ParserFinding]]:
        """Return the document's type, or ``None`` plus the findings that prevented finding it."""
        known = ", ".join(self._doc_types)
        if "type" not in document.front_matter:
            return None, [
                ParserFinding(
                    code="type-missing",
                    message="front matter has no 'type' key",
                    hint=f"add 'type: <type>', with one of: {known}",
                )
            ]
        declared = document.front_matter["type"]
        if not isinstance(declared, str):
            return None, [
                ParserFinding(
                    code="type-not-text",
                    message="'type' is not text",
                    hint=f"set 'type' to one of: {known}",
                )
            ]
        doc_type = self._doc_types.get(declared)
        if doc_type is None:
            return None, [
                ParserFinding(
                    code="type-unknown",
                    message=f"unknown type '{declared}'",
                    hint=f"set 'type' to one of: {known} (lowercase, exact)",
                )
            ]
        return doc_type, []
