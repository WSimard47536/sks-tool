"""The validator for ``overview`` documents.

- The summary and the purpose each fit on one line and are at most 200
  characters long, counted as written.
- The system diagram follows the diagram rules of ``sks_tool.validators.diagram``;
  its file may have any name.

A missing section has already been reported by the parser and is not checked
again. Any number of overviews may be checked together, for example one per
subsystem.
"""

from sks_tool.docs.overview.doc import OverviewDoc, TextSection
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.diagram import check_diagram

TEXT_MAX_CHARACTERS = 200


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
            findings += check_diagram(doc.system_diagram, doc.document.path.parent, ("system diagram",))
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
