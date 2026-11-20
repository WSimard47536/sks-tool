"""The parser for one requirement block.

``RequirementsParser`` splits the document into blocks, each starting at a
level-2 heading, and hands each one to ``RequirementParser``. The block is
read as described in ``sks_tool.parsers.req_spec_shared``; a requirement has
no diagram.
"""

from collections.abc import Sequence

from sks_tool.docs.req_spec_shared import RATIONALE
from sks_tool.docs.requirements.requirement.block import FIELDS, Requirement, RequirementType
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import Line
from sks_tool.parsers.req_spec_shared import read_tracked_block


class RequirementParser:
    """Reads one requirement block into a ``Requirement``."""

    def parse(self, heading: Line, lines: Sequence[Line]) -> tuple[Requirement | None, list[ParserFinding]]:
        """Return the requirement, or ``None`` plus the findings that prevented reading it.

        ``heading`` is the block's heading line, already stripped of its
        ``##`` marker; ``lines`` are the lines up to the next heading.
        """
        heading_line, requirement_id = heading
        if not requirement_id:
            return None, [
                ParserFinding(
                    code="requirement-id-missing",
                    message="a requirement heading has no ID",
                    hint="write the requirement's ID after '## '",
                    line=heading_line,
                )
            ]
        block, findings = read_tracked_block(
            "requirement", heading, lines, fields=FIELDS, labels=list(RequirementType), diagram=False
        )
        if block is None:
            return None, findings
        rationale = block.fields.get(RATIONALE)
        requirement = Requirement(
            id=requirement_id,
            type=None if block.type is None else block.type[1],
            status=None if block.status is None else block.status[1],
            statement=block.statement_text(),
            rationale=None if rationale is None else rationale[1],
            criteria=tuple(block.criteria),
            line=heading_line,
            type_line=None if block.type is None else block.type[0],
            status_line=None if block.status is None else block.status[0],
            statement_line=block.statement[0][0],
            rationale_line=None if rationale is None else rationale[0],
        )
        return requirement, findings
