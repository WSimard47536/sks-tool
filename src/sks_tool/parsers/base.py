"""The ``Parser`` interface, and the root parser shared by every document.

A parser reads a ``Document`` into a structure. It returns the structure, or
``None`` plus at least one finding saying why it could not; returning ``None``
without a finding is a bug in the parser, and the pipeline stops on it. A
parser may also return a structure together with findings, for problems it
could work around: the structure is then still validated.

``CommonParser`` reads the part shared by every document, its front matter
keys (``sks_tool.docs.base.Metadata``). The ``type`` key selects the parser
and validator for the rest.
"""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from sks_tool.docs.base import Metadata
from sks_tool.document import Document
from sks_tool.findings import ParserFinding

if TYPE_CHECKING:
    # Imported for type checking only: the registry imports every type's
    # parser, so a runtime import here could create an import cycle.
    from sks_tool.doctypes import DocType


class Parser[T](Protocol):
    """Reads a ``Document`` into a structure of type ``T``."""

    def parse(self, document: Document, metadata: Metadata, /) -> tuple[T | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        ...


class CommonParser:
    """Reads the front matter keys shared by every document."""

    def __init__(self, doc_types: Mapping[str, "DocType[Any]"]) -> None:
        self._doc_types = doc_types

    def parse(self, document: Document) -> tuple[Metadata, list[ParserFinding]]:
        """Return the metadata, and the findings for the keys that are missing or unusable.

        ``Metadata.doc_type`` is ``None`` when the type is unusable; the
        document can then not be read any further.
        """
        findings: list[ParserFinding] = []
        doc_type = self._parse_type(document, findings)
        title = _parse_text(
            document,
            "title",
            "add 'title: <title>', of at most 5 words",
            findings,
        )
        description = _parse_text(
            document,
            "description",
            "add 'description: <what the document contains>', of at most 100 words",
            findings,
        )
        return Metadata(doc_type=doc_type, title=title, description=description), findings

    def _parse_type(self, document: Document, findings: list[ParserFinding]) -> str | None:
        known = ", ".join(self._doc_types)
        if "type" not in document.front_matter:
            findings.append(
                ParserFinding(
                    code="type-missing",
                    message="front matter has no 'type' key",
                    hint=f"add 'type: <type>', with one of: {known}",
                )
            )
            return None
        declared = document.front_matter["type"]
        if not isinstance(declared, str):
            findings.append(
                ParserFinding(
                    code="type-not-text",
                    message="'type' is not text",
                    hint=f"set 'type' to one of: {known}",
                )
            )
            return None
        if declared not in self._doc_types:
            findings.append(
                ParserFinding(
                    code="type-unknown",
                    message=f"unknown type '{declared}'",
                    hint=f"set 'type' to one of: {known} (lowercase, exact)",
                )
            )
            return None
        return declared


def _parse_text(document: Document, key: str, add_hint: str, findings: list[ParserFinding]) -> str | None:
    """Read the text value of front matter ``key``, or report why it is unusable."""
    if key not in document.front_matter:
        findings.append(ParserFinding(code=f"{key}-missing", message=f"front matter has no '{key}' key", hint=add_hint))
        return None
    value = document.front_matter[key]
    if value is None:
        # YAML reads an empty value ("title:") as null: the key is there but
        # empty, which the validator reports.
        return ""
    if not isinstance(value, str):
        findings.append(
            ParserFinding(
                code=f"{key}-not-text",
                message=f"'{key}' is not text",
                hint=f"write '{key}' as text; put it in quotes if YAML reads it as a number, a date or a list",
            )
        )
        return None
    return value
