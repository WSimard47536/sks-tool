"""The parser for ``specs`` documents.

The blocks of a ``specs`` document are not defined yet, so this parser reads
every body successfully. Parsing for the part shared by every document type
belongs in ``sks_tool.parsers.base``.
"""

from sks_tool.docs.base import Metadata
from sks_tool.docs.specs.doc import SpecsDoc
from sks_tool.document import Document
from sks_tool.findings import ParserFinding


class SpecsParser:
    """Reads a ``specs`` document into a ``SpecsDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[SpecsDoc | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        return SpecsDoc(metadata=metadata, document=document), []
