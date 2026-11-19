"""The parser for ``requirements`` documents.

The body of a ``requirements`` document is a sequence of requirement blocks,
each starting at a level-2 heading (``## <ID>``). Outside the blocks only
blank lines and ``<!-- comments -->`` are allowed. This parser removes the
comments, splits the body into blocks and hands each block to
``RequirementParser``.

Comments must take whole lines; they may span several lines.
"""

import re
from collections.abc import Iterable

from sks_tool.docs.base import Metadata
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.document import Document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.requirements.requirement.parser import Line, RequirementParser

REQUIREMENT_HEADING_LEVEL = 2

_HEADING = re.compile(r"(?P<marks>#{1,6})(?:[ \t]+(?P<text>.*?))?(?:[ \t]+#+)?[ \t]*")
_COMMENT_OPEN = "<!--"
_COMMENT_CLOSE = "-->"


class RequirementsParser:
    """Reads a ``requirements`` document into a ``RequirementsDoc``."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[RequirementsDoc | None, list[ParserFinding]]:
        """Return the structure, with the findings for the blocks it could not read."""
        numbered = list(enumerate(document.body.split("\n"), start=document.body_line))
        lines, findings = _blank_comments(numbered)

        blocks: list[tuple[Line, list[Line]]] = []
        previous_stray = False
        for number, text in lines:
            heading = _HEADING.fullmatch(text)
            if heading is not None:
                previous_stray = False
                level = len(heading["marks"])
                if level == REQUIREMENT_HEADING_LEVEL:
                    blocks.append(((number, (heading["text"] or "").strip()), []))
                else:
                    findings.append(
                        ParserFinding(
                            code="heading-wrong-level",
                            message=f"a level-{level} heading; requirement IDs are level-2 headings",
                            hint="write it as '## <ID>' to start a requirement, or remove it; "
                            "the document's title belongs in the front matter",
                            line=number,
                        )
                    )
                continue
            if blocks:
                blocks[-1][1].append((number, text))
                continue
            if text.strip() and not previous_stray:
                # Only the first line of each stray paragraph is reported.
                findings.append(
                    ParserFinding(
                        code="text-outside-requirement",
                        message="text outside any requirement",
                        hint="start a requirement with a '## <ID>' heading, or put the text in a <!-- comment -->; "
                        "the document's description belongs in the front matter",
                        line=number,
                    )
                )
            previous_stray = bool(text.strip())

        requirements: list[Requirement] = []
        block_parser = RequirementParser()
        for heading_line, block_lines in blocks:
            requirement, block_findings = block_parser.parse(heading_line, block_lines)
            findings += block_findings
            if requirement is not None:
                requirements.append(requirement)

        doc = RequirementsDoc(metadata=metadata, document=document, requirements=tuple(requirements))
        return doc, findings


def _blank_comments(lines: Iterable[Line]) -> tuple[list[Line], list[ParserFinding]]:
    """Remove every comment, so a comment line reads as a blank line and separates paragraphs.

    A comment sharing its line with other text is reported; the comment is
    still removed and the other text kept, so it is checked like any text
    (a comment after an ID does not become part of the ID).
    """
    result: list[Line] = []
    findings: list[ParserFinding] = []
    open_line: int | None = None
    for number, text in lines:
        touched = open_line is not None
        kept: list[str] = []
        rest = text
        while rest:
            if open_line is not None:
                end = rest.find(_COMMENT_CLOSE)
                if end < 0:
                    break
                rest = rest[end + len(_COMMENT_CLOSE) :]
                open_line = None
                continue
            start = rest.find(_COMMENT_OPEN)
            if start < 0:
                kept.append(rest)
                break
            kept.append(rest[:start])
            rest = rest[start + len(_COMMENT_OPEN) :]
            open_line = number
            touched = True
        if not touched:
            result.append((number, text))
            continue
        remaining = "".join(kept)
        if remaining.strip():
            findings.append(
                ParserFinding(
                    code="comment-not-whole-line",
                    message="a comment shares its line with other text",
                    hint="a comment must take whole lines: move the comment or the text to its own line",
                    line=number,
                )
            )
        result.append((number, remaining if remaining.strip() else ""))
    if open_line is not None:
        findings.append(
            ParserFinding(
                code="comment-unterminated",
                message="a comment is never closed",
                hint=f"close it with '{_COMMENT_CLOSE}'",
                line=open_line,
            )
        )
    return result, findings
