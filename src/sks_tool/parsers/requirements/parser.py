"""The parser for ``requirements`` documents.

The body of a ``requirements`` document is a sequence of requirement blocks,
each starting at a level-2 heading (``## <ID>``), with only blank lines and
``<!-- comments -->`` outside them (see ``sks_tool.parsers.markdown``). This
parser splits the body into blocks and hands each one to
``RequirementParser``.
"""

from sks_tool.docs.base import Metadata
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.document import Document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import EntryKind, read_blocks
from sks_tool.parsers.requirements.requirement.parser import RequirementParser

REQUIREMENT = EntryKind(name="requirement", heading="<ID>", headings_are="requirement IDs")


class RequirementsParser:
    """Reads a ``requirements`` document into a ``RequirementsDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[RequirementsDoc | None, list[ParserFinding]]:
        """Return the structure, with the findings for the blocks it could not read."""
        blocks, findings = read_blocks(document, REQUIREMENT)
        requirements: list[Requirement] = []
        block_parser = RequirementParser()
        for block in blocks:
            requirement, block_findings = block_parser.parse(block.heading, block.lines)
            findings += block_findings
            if requirement is not None:
                requirements.append(requirement)

        doc = RequirementsDoc(metadata=metadata, document=document, requirements=tuple(requirements))
        return doc, findings
