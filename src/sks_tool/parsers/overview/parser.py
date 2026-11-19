"""The parser for ``overview`` documents.

The blocks of a ``overview`` document are not defined yet, so this parser reads
every document successfully. Parsing for the part shared by every document
type belongs in ``sks_tool.parsers.base``.
"""

from sks_tool.docs.overview.doc import OverviewDoc
from sks_tool.document import Document
from sks_tool.findings import ParserFinding


class OverviewParser:
    """Reads a ``overview`` document into a ``OverviewDoc``."""

    def parse(self, document: Document) -> tuple[OverviewDoc | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        return OverviewDoc(document=document), []
