"""The parser for ``glossary`` documents.

The blocks of a ``glossary`` document are not defined yet, so this parser reads
every body successfully. Parsing for the part shared by every document type
belongs in ``sks_tool.parsers.base``.
"""

from sks_tool.docs.base import Metadata
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.document import Document
from sks_tool.findings import ParserFinding


class GlossaryParser:
    """Reads a ``glossary`` document into a ``GlossaryDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[GlossaryDoc | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        return GlossaryDoc(metadata=metadata, document=document), []
