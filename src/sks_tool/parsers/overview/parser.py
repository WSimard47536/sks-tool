"""The parser for ``overview`` documents.

The body of an ``overview`` document is its three sections, each starting at
a level-2 heading, with only blank lines and ``<!-- comments -->`` outside
them (see ``sks_tool.parsers.markdown``):

- ``Summary`` and ``Purpose`` each hold one paragraph;
- ``System diagram`` holds one Markdown image on its own line,
  ``![<alt>](<path>)``.

Each heading must appear exactly once, in that order, and the heading names
are matched exactly. A missing, unknown, repeated or misplaced section, a
section without its content, and any other content are parse findings; the
rest of the document is still read.
"""

import re
from collections.abc import Sequence

from sks_tool.docs.base import Metadata
from sks_tool.docs.overview.doc import PURPOSE, SECTIONS, SUMMARY, SYSTEM_DIAGRAM, Diagram, OverviewDoc, TextSection
from sks_tool.document import Document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import Block, EntryKind, Line, read_blocks

SECTION = EntryKind(name="section", heading="<section>", headings_are="section headings")

_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^()\s]+)\)")


class OverviewParser:
    """Reads an ``overview`` document into an ``OverviewDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[OverviewDoc | None, list[ParserFinding]]:
        """Return the structure, with the findings for what could not be read."""
        blocks, findings = read_blocks(document, SECTION)
        known = ", ".join(f"'{name}'" for name in SECTIONS)

        sections: dict[str, Block] = {}
        last_index = -1
        for block in blocks:
            number, heading = block.heading
            if heading not in SECTIONS:
                findings.append(
                    ParserFinding(
                        code="overview-section-unknown",
                        message=f"unknown section '{heading}'",
                        hint=f"an overview has exactly these sections, in this order: {known}",
                        line=number,
                    )
                )
                continue
            if heading in sections:
                findings.append(
                    ParserFinding(
                        code="overview-section-repeated",
                        message=f"the '{heading}' section appears more than once",
                        hint=f"keep a single '{heading}' section; the first one, on line "
                        f"{sections[heading].heading[0]}, is used",
                        line=number,
                    )
                )
                continue
            index = SECTIONS.index(heading)
            if index < last_index:
                findings.append(
                    ParserFinding(
                        code="overview-section-out-of-order",
                        message=f"the '{heading}' section comes after '{SECTIONS[last_index]}'",
                        hint=f"put the sections in this order: {known}",
                        line=number,
                    )
                )
            last_index = max(last_index, index)
            sections[heading] = block

        for heading in SECTIONS:
            if heading not in sections:
                findings.append(
                    ParserFinding(
                        code="overview-section-missing",
                        message=f"the overview has no '{heading}' section",
                        hint=f"add a '## {heading}' section; an overview has: {known}",
                    )
                )

        summary = _read_paragraph(sections.get(SUMMARY), findings)
        purpose = _read_paragraph(sections.get(PURPOSE), findings)
        diagram = _read_diagram(sections.get(SYSTEM_DIAGRAM), findings)
        doc = OverviewDoc(
            metadata=metadata,
            document=document,
            summary=summary,
            purpose=purpose,
            system_diagram=diagram,
        )
        return doc, findings


def _report_unexpected(heading: str, lines: Sequence[Line], findings: list[ParserFinding], what: str) -> None:
    """Report the first line of each stray paragraph in a section."""
    previous_stray = False
    for number, text in lines:
        if not text.strip():
            previous_stray = False
            continue
        if not previous_stray:
            findings.append(
                ParserFinding(
                    code="overview-text-unexpected",
                    message=f"unexpected content in the '{heading}' section",
                    hint=f"the '{heading}' section holds {what} only; remove this or put it in a <!-- comment -->",
                    line=number,
                )
            )
        previous_stray = True


def _read_paragraph(block: Block | None, findings: list[ParserFinding]) -> TextSection | None:
    """Read a section's single paragraph; report anything after it."""
    if block is None:
        return None
    heading_line, heading = block.heading
    paragraph: list[Line] = []
    rest: list[Line] = []
    for number, text in block.lines:
        stripped = text.strip()
        is_bullet = stripped == "-" or stripped.startswith(("- ", "-\t"))
        if rest or is_bullet or (paragraph and not stripped):
            # A blank line ends the paragraph; a list is never part of it.
            rest.append((number, text))
        elif stripped:
            paragraph.append((number, stripped))
    _report_unexpected(heading, rest, findings, "one paragraph")
    if not paragraph:
        findings.append(
            ParserFinding(
                code="overview-section-empty",
                message=f"the '{heading}' section is empty",
                hint=f"write the {heading.lower()} as one paragraph under its heading",
                line=heading_line,
            )
        )
        return None
    return TextSection(text="\n".join(text for _, text in paragraph), line=paragraph[0][0])


def _read_diagram(block: Block | None, findings: list[ParserFinding]) -> Diagram | None:
    """Read the section's single image; report anything else."""
    if block is None:
        return None
    heading_line, heading = block.heading
    images: list[Diagram] = []
    others: list[Line] = []
    for number, text in block.lines:
        match = _IMAGE.fullmatch(text.strip())
        if match is not None:
            images.append(Diagram(alt=match["alt"], path=match["path"], line=number))
        else:
            others.append((number, text))
    _report_unexpected(heading, others, findings, "the diagram image, written as ![<alt text>](<file>.drawio.svg),")
    if not images:
        findings.append(
            ParserFinding(
                code="diagram-missing",
                message=f"the '{heading}' section has no image",
                hint="show the diagram as a Markdown image on its own line: ![System diagram](system_diagram.drawio.svg)",
                line=heading_line,
            )
        )
        return None
    for extra in images[1:]:
        findings.append(
            ParserFinding(
                code="diagram-repeated",
                message=f"the '{heading}' section has more than one image",
                hint=f"keep a single diagram; the first one, on line {images[0].line}, is used",
                line=extra.line,
            )
        )
    return images[0]
