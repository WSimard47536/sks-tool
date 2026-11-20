"""The structure of an ``overview`` document.

An ``overview`` document has exactly three sections, in this order, and
nothing else; blank lines and ``<!-- comments -->`` may appear between them::

    ## Summary

    What the system is, on one line.

    ## Purpose

    Why it is built, on one line.

    ## System diagram

    ![System diagram](system_diagram.drawio.svg)

The diagram is a ``.drawio.svg`` file (see ``sks_tool.docs.diagram``).
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.docs.diagram import Diagram
from sks_tool.document import Document

SUMMARY = "Summary"
PURPOSE = "Purpose"
SYSTEM_DIAGRAM = "System diagram"
SECTIONS = (SUMMARY, PURPOSE, SYSTEM_DIAGRAM)
"""The section headings, in the order they must appear."""


@dataclass(frozen=True)
class TextSection:
    """A section holding one paragraph of text."""

    text: str
    """The paragraph as written; lines are joined with ``\\n`` if it spans several."""
    line: int
    """1-based line where the paragraph starts."""


@dataclass(frozen=True)
class OverviewDoc:
    """An ``overview`` document read into its structure.

    A section is ``None`` when it is missing or empty; the parser has then
    already reported why.
    """

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
    summary: TextSection | None
    purpose: TextSection | None
    system_diagram: Diagram | None
