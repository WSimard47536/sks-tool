"""The parser for ``requirements`` documents.

The blocks of a ``requirements`` document are not defined yet, so this parser reads
every document successfully. Parsing for the part shared by every document
type belongs in ``sks_tool.parsers.base``.
"""

from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.document import Document
from sks_tool.findings import ParserFinding


class RequirementsParser:
    """Reads a ``requirements`` document into a ``RequirementsDoc``."""

    def parse(self, document: Document) -> tuple[RequirementsDoc | None, list[ParserFinding]]:
        """Return the structure, or ``None`` plus the findings that prevented reading it."""
        return RequirementsDoc(document=document), []
