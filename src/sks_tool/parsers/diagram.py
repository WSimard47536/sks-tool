"""Reading a diagram image, for any document type that shows diagrams.

A diagram is a Markdown image alone on its line: ``![<alt>](<path>)``. The
path may not contain spaces or parentheses. Whether the path points to a
valid ``.drawio.svg`` file is checked by ``sks_tool.validators.diagram``.
"""

import re

from sks_tool.docs.diagram import Diagram

_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^()\s]+)\)")

IMAGE_SYNTAX = "![<alt text>](<file>.drawio.svg)"
"""How an image is written, for hints."""


def read_image(number: int, text: str) -> Diagram | None:
    """Return the diagram if line ``text`` is exactly one Markdown image, else ``None``."""
    match = _IMAGE.fullmatch(text.strip())
    if match is None:
        return None
    return Diagram(alt=match["alt"], path=match["path"], line=number)
