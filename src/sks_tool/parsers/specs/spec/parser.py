"""The parser for one spec block.

``SpecsParser`` splits the document into blocks, each starting at a level-2
heading, and hands each one to ``SpecParser``. The block is read as
described in ``sks_tool.parsers.req_spec_shared``; a spec may end with a
diagram, and its rationale is required.
"""

from collections.abc import Sequence

from sks_tool.docs.req_spec_shared import RATIONALE
from sks_tool.docs.specs.spec.block import FIELDS, Spec, SpecType
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import Line
from sks_tool.parsers.req_spec_shared import read_tracked_block


class SpecParser:
    """Reads one spec block into a ``Spec``."""

    def parse(self, heading: Line, lines: Sequence[Line]) -> tuple[Spec | None, list[ParserFinding]]:
        """Return the spec, or ``None`` plus the findings that prevented reading it.

        ``heading`` is the block's heading line, already stripped of its
        ``##`` marker; ``lines`` are the lines up to the next heading.
        """
        heading_line, spec_id = heading
        if not spec_id:
            return None, [
                ParserFinding(
                    code="spec-id-missing",
                    message="a spec heading has no ID",
                    hint="write the spec's ID after '## '",
                    line=heading_line,
                )
            ]
        block, findings = read_tracked_block("spec", heading, lines, fields=FIELDS, labels=list(SpecType), diagram=True)
        if block is None:
            return None, findings
        rationale = block.fields.get(RATIONALE)
        if rationale is None:
            findings.append(
                ParserFinding(
                    code="spec-rationale-missing",
                    message=f"spec {spec_id} has no rationale",
                    hint="add '- Rationale: <why it was decided>' after the statement; a spec records why",
                    line=block.statement[0][0],
                )
            )
        spec = Spec(
            id=spec_id,
            type=None if block.type is None else block.type[1],
            status=None if block.status is None else block.status[1],
            statement=block.statement_text(),
            rationale=None if rationale is None else rationale[1],
            criteria=tuple(block.criteria),
            diagram=block.diagram,
            line=heading_line,
            type_line=None if block.type is None else block.type[0],
            status_line=None if block.status is None else block.status[0],
            statement_line=block.statement[0][0],
            rationale_line=None if rationale is None else rationale[0],
        )
        return spec, findings
