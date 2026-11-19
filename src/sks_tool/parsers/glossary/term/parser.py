"""The parser for one term block.

``GlossaryParser`` splits the document into blocks, each starting at a
level-2 heading, and hands each one to ``TermParser``. A block holds only
the definition: the first paragraph after the heading.

Blank lines separate paragraphs; comments have already been replaced by blank
lines. Stray text after the definition is reported and the term is kept; a
block without a term or a definition cannot be read and is dropped.
"""

from collections.abc import Sequence

from sks_tool.docs.glossary.term.block import Term
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import Line


class TermParser:
    """Reads one term block into a ``Term``."""

    def parse(self, heading: Line, lines: Sequence[Line]) -> tuple[Term | None, list[ParserFinding]]:
        """Return the term, or ``None`` plus the findings that prevented reading it.

        ``heading`` is the block's heading line, already stripped of its
        ``##`` marker; ``lines`` are the lines up to the next heading.
        """
        heading_line, term = heading
        if not term:
            return None, [
                ParserFinding(
                    code="term-missing",
                    message="a glossary heading has no term",
                    hint="write the term after '## '",
                    line=heading_line,
                )
            ]

        findings: list[ParserFinding] = []
        definition: list[Line] = []
        # "before" the definition, "in" it, or "after" it.
        state = "before"
        previous_stray = False
        for number, text in lines:
            stripped = text.strip()
            if not stripped:
                if state == "in":
                    state = "after"
                previous_stray = False
                continue
            is_bullet = stripped == "-" or stripped.startswith(("- ", "-\t"))
            if state == "before" and not is_bullet:
                state = "in"
            if state == "in" and not is_bullet:
                definition.append((number, stripped))
                continue
            # Anything else, a list or a second paragraph, does not belong.
            state = "after"
            if not previous_stray:
                # Only the first line of each stray paragraph is reported.
                findings.append(
                    ParserFinding(
                        code="glossary-text-unexpected",
                        message=f"unexpected text in term '{term}'",
                        hint="a term has a single definition paragraph; remove this text or put it in a <!-- comment -->",
                        line=number,
                    )
                )
            previous_stray = True

        if not definition:
            findings.append(
                ParserFinding(
                    code="definition-missing",
                    message=f"term '{term}' has no definition",
                    hint="write the definition as the paragraph right under the term",
                    line=heading_line,
                )
            )
            return None, findings

        return (
            Term(
                term=term,
                definition="\n".join(text for _, text in definition),
                line=heading_line,
                definition_line=definition[0][0],
            ),
            findings,
        )
