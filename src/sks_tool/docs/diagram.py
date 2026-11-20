"""The structure of a diagram, as shown by any document type that has one.

A diagram is a Markdown image on its own line, ``![<alt>](<path>)``, pointing
to a ``.drawio.svg`` file: an SVG image that also carries the editable
draw.io diagram, so the same file is edited in draw.io (for example with the
Draw.io Integration extension for VS Code) and rendered on the page.
"""

from dataclasses import dataclass

DIAGRAM_SUFFIX = ".drawio.svg"


@dataclass(frozen=True)
class Diagram:
    """A diagram shown as a Markdown image: ``![<alt>](<path>)``."""

    alt: str
    path: str
    """The image path as written, relative to the document's folder."""
    line: int
    """1-based line of the image."""
