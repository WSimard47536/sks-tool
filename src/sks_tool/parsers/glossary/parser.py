"""The parser for ``glossary`` documents.

The body of a ``glossary`` document is a sequence of term blocks, each
starting at a level-2 heading (``## <term>``), with only blank lines and
``<!-- comments -->`` outside them (see ``sks_tool.parsers.markdown``). This
parser splits the body into blocks and hands each one to ``TermParser``.
"""

from sks_tool.docs.base import Metadata
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.docs.glossary.term.block import Term
from sks_tool.document import Document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.glossary.term.parser import TermParser
from sks_tool.parsers.markdown import EntryKind, read_blocks

TERM = EntryKind(name="term", heading="<term>", headings_are="terms")


class GlossaryParser:
    """Reads a ``glossary`` document into a ``GlossaryDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[GlossaryDoc | None, list[ParserFinding]]:
        """Return the structure, with the findings for the blocks it could not read."""
        blocks, findings = read_blocks(document, TERM)
        terms: list[Term] = []
        block_parser = TermParser()
        for block in blocks:
            term, block_findings = block_parser.parse(block.heading, block.lines)
            findings += block_findings
            if term is not None:
                terms.append(term)

        return GlossaryDoc(metadata=metadata, document=document, terms=tuple(terms)), findings
