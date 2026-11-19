"""Markdown reading shared by the parsers of documents made of ``##`` blocks.

A document such as ``requirements`` or ``glossary`` is a sequence of entries,
each starting at a level-2 heading. Outside the entries only blank lines and
``<!-- comments -->`` are allowed. Comments may span several lines but must
take whole lines.

``read_blocks`` removes the comments and splits a document's body into its
blocks, reporting what does not belong; each type's parser then reads the
blocks themselves.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass

from sks_tool.document import Document
from sks_tool.findings import ParserFinding

type Line = tuple[int, str]
"""A line of the file: its 1-based number and its text."""

BLOCK_HEADING_LEVEL = 2

_HEADING = re.compile(r"(?P<marks>#{1,6})(?:[ \t]+(?P<text>.*?))?(?:[ \t]+#+)?[ \t]*")
_COMMENT_OPEN = "<!--"
_COMMENT_CLOSE = "-->"


@dataclass(frozen=True)
class EntryKind:
    """How a type's entries are named in findings."""

    name: str
    """What one entry is, e.g. ``requirement``; also used in finding codes."""
    heading: str
    """What the heading holds, e.g. ``<ID>``."""
    headings_are: str
    """What the headings are, for messages, e.g. ``requirement IDs``."""


@dataclass(frozen=True)
class Block:
    """One entry's lines, up to the next level-2 heading."""

    heading: Line
    """The heading's line, its text stripped of the ``##`` marker."""
    lines: list[Line]


def read_blocks(document: Document, kind: EntryKind) -> tuple[list[Block], list[ParserFinding]]:
    """Return the body's blocks, with comments removed, and the findings for what does not belong."""
    numbered = list(enumerate(document.body.split("\n"), start=document.body_line))
    lines, findings = blank_comments(numbered)

    blocks: list[Block] = []
    previous_stray = False
    for number, text in lines:
        heading = _HEADING.fullmatch(text)
        if heading is not None:
            previous_stray = False
            level = len(heading["marks"])
            if level == BLOCK_HEADING_LEVEL:
                blocks.append(Block(heading=(number, (heading["text"] or "").strip()), lines=[]))
            else:
                findings.append(
                    ParserFinding(
                        code="heading-wrong-level",
                        message=f"a level-{level} heading; {kind.headings_are} are level-2 headings",
                        hint=f"write it as '## {kind.heading}' to start a {kind.name}, or remove it; "
                        "the document's title belongs in the front matter",
                        line=number,
                    )
                )
            continue
        if blocks:
            blocks[-1].lines.append((number, text))
            continue
        if text.strip() and not previous_stray:
            # Only the first line of each stray paragraph is reported.
            findings.append(
                ParserFinding(
                    code=f"text-outside-{kind.name}",
                    message=f"text outside any {kind.name}",
                    hint=f"start a {kind.name} with a '## {kind.heading}' heading, or put the text in a "
                    "<!-- comment -->; the document's description belongs in the front matter",
                    line=number,
                )
            )
        previous_stray = bool(text.strip())
    return blocks, findings


def blank_comments(lines: Iterable[Line]) -> tuple[list[Line], list[ParserFinding]]:
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
