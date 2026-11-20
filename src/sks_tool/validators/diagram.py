"""Checking a diagram's file, for any document type that shows diagrams.

The image path must be relative, resolved from the document's folder, and
point to an existing ``.drawio.svg`` file that carries an editable draw.io
diagram: draw.io stores it, as an ``<mxfile>``, in the ``content`` attribute
of the SVG. A document type may also require a file name, such as a spec's
diagram being named after the spec's ID.
"""

import re
from pathlib import Path, PurePosixPath

from sks_tool.docs.diagram import DIAGRAM_SUFFIX, Diagram
from sks_tool.findings import ValidatorFinding

_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
"""A URL scheme such as ``https:``, or a Windows drive such as ``C:``."""
_DRAWIO_CONTENT = re.compile(r"<svg\b[^>]*\bcontent=\"[^\"]*mxfile", re.DOTALL)


def check_diagram(
    diagram: Diagram, folder: Path, location: tuple[str, ...], expected_name: str | None = None
) -> list[ValidatorFinding]:
    """Return the rules the diagram breaks; the first one found is reported alone.

    ``folder`` is the document's folder, ``location`` how findings name the
    diagram, and ``expected_name`` the file name the diagram must have, if any.
    """

    def finding(code: str, message: str, hint: str) -> list[ValidatorFinding]:
        return [ValidatorFinding(code=code, message=message, hint=hint, location=location, line=diagram.line)]

    path = diagram.path
    if _URL.match(path) or PurePosixPath(path).is_absolute() or path.startswith("\\"):
        return finding(
            "diagram-path-not-relative",
            f"'{path}' is not a relative path",
            "point to a file in the repository, relative to this document's folder",
        )
    if not path.endswith(DIAGRAM_SUFFIX):
        return finding(
            "diagram-not-drawio-svg",
            f"'{path}' is not a {DIAGRAM_SUFFIX} file",
            f"save the diagram from draw.io as a {DIAGRAM_SUFFIX} file, which stays editable and renders as an image",
        )
    if expected_name is not None and PurePosixPath(path).name != expected_name:
        return finding(
            "diagram-name-mismatch",
            f"'{PurePosixPath(path).name}' is not named '{expected_name}'",
            f"rename the file to '{expected_name}' and update the image path",
        )
    file = folder / path
    if not file.is_file():
        return finding(
            "diagram-file-not-found",
            f"'{path}' does not exist",
            "check the path; it is relative to this document's folder",
        )
    try:
        text = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = ""
    if not _DRAWIO_CONTENT.search(text):
        return finding(
            "diagram-not-editable",
            f"'{path}' does not carry an editable draw.io diagram",
            f"create or save it with draw.io (e.g. the Draw.io Integration extension for VS Code) as {DIAGRAM_SUFFIX}; "
            "a plain SVG renamed to that extension cannot be edited",
        )
    return []
