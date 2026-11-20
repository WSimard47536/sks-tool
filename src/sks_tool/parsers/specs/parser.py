"""The parser for ``specs`` documents.

The body of a ``specs`` document is a sequence of spec blocks, each starting
at a level-2 heading (``## <ID>``), with only blank lines and
``<!-- comments -->`` outside them (see ``sks_tool.parsers.markdown``). This
parser splits the body into blocks and hands each one to ``SpecParser``.
"""

from sks_tool.docs.base import Metadata
from sks_tool.docs.specs.doc import SpecsDoc
from sks_tool.docs.specs.spec.block import Spec
from sks_tool.document import Document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import EntryKind, read_blocks
from sks_tool.parsers.specs.spec.parser import SpecParser

SPEC = EntryKind(name="spec", heading="<ID>", headings_are="spec IDs")


class SpecsParser:
    """Reads a ``specs`` document into a ``SpecsDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[SpecsDoc | None, list[ParserFinding]]:
        """Return the structure, with the findings for the blocks it could not read."""
        blocks, findings = read_blocks(document, SPEC)
        specs: list[Spec] = []
        block_parser = SpecParser()
        for block in blocks:
            spec, block_findings = block_parser.parse(block.heading, block.lines)
            findings += block_findings
            if spec is not None:
                specs.append(spec)

        return SpecsDoc(metadata=metadata, document=document, specs=tuple(specs)), findings
