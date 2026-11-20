"""The validator for ``overview`` documents.

- The summary and the purpose each fit on one line and are at most 200
  characters long, counted as written.
- The system diagram is a relative path, resolved from the document's folder,
  to an existing ``.drawio.svg`` file that carries an editable draw.io
  diagram: draw.io stores it, as an ``<mxfile>``, in the ``content``
  attribute of the SVG.

A missing section has already been reported by the parser and is not checked
again. Any number of overviews may be checked together, for example one per
subsystem.
"""

import re
from pathlib import Path, PurePosixPath

from sks_tool.docs.overview.doc import Diagram, OverviewDoc, TextSection
from sks_tool.findings import ValidatorFinding

TEXT_MAX_CHARACTERS = 200
DIAGRAM_SUFFIX = ".drawio.svg"

_URL = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
"""A URL scheme such as ``https:``, or a Windows drive such as ``C:``."""
_DRAWIO_CONTENT = re.compile(r"<svg\b[^>]*\bcontent=\"[^\"]*mxfile", re.DOTALL)


class OverviewValidator:
    """Checks an ``OverviewDoc``."""

    def validate(self, doc: OverviewDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        findings: list[ValidatorFinding] = []
        if doc.summary is not None:
            findings += _check_text("summary", doc.summary)
        if doc.purpose is not None:
            findings += _check_text("purpose", doc.purpose)
        if doc.system_diagram is not None:
            findings += _check_diagram(doc.system_diagram, doc.document.path.parent)
        return findings


def _check_text(key: str, section: TextSection) -> list[ValidatorFinding]:
    findings: list[ValidatorFinding] = []

    def finding(code: str, message: str, hint: str) -> ValidatorFinding:
        return ValidatorFinding(code=code, message=message, hint=hint, location=(key,), line=section.line)

    line_count = section.text.count("\n") + 1
    if line_count > 1:
        findings.append(finding(f"{key}-not-one-line", f"spans {line_count} lines", f"write the {key} on a single line"))
    length = len(" ".join(section.text.split("\n")))
    if length > TEXT_MAX_CHARACTERS:
        findings.append(
            finding(
                f"{key}-too-long",
                f"is {length} characters long; the limit is {TEXT_MAX_CHARACTERS}",
                f"shorten the {key}; details belong in other documents",
            )
        )
    return findings


def _check_diagram(diagram: Diagram, folder: Path) -> list[ValidatorFinding]:
    def finding(code: str, message: str, hint: str) -> ValidatorFinding:
        return ValidatorFinding(code=code, message=message, hint=hint, location=("system diagram",), line=diagram.line)

    path = diagram.path
    if _URL.match(path) or PurePosixPath(path).is_absolute() or path.startswith("\\"):
        return [
            finding(
                "diagram-path-not-relative",
                f"'{path}' is not a relative path",
                "point to a file in the repository, relative to this document's folder",
            )
        ]
    if not path.endswith(DIAGRAM_SUFFIX):
        return [
            finding(
                "diagram-not-drawio-svg",
                f"'{path}' is not a {DIAGRAM_SUFFIX} file",
                f"save the diagram from draw.io as a {DIAGRAM_SUFFIX} file, which stays editable and renders as an image",
            )
        ]
    file = folder / path
    if not file.is_file():
        return [
            finding(
                "diagram-file-not-found",
                f"'{path}' does not exist",
                "check the path; it is relative to this document's folder",
            )
        ]
    try:
        text = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = ""
    if not _DRAWIO_CONTENT.search(text):
        return [
            finding(
                "diagram-not-editable",
                f"'{path}' does not carry an editable draw.io diagram",
                f"create or save it with draw.io (e.g. the Draw.io Integration extension for VS Code) as {DIAGRAM_SUFFIX}; "
                "a plain SVG renamed to that extension cannot be edited",
            )
        ]
    return []
