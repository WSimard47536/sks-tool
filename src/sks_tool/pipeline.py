"""The pipeline that checks one document: parse it, then validate it.

``check_file`` is the single entry point. It runs, in order:

1. ``load_document``: split the file into front matter and body;
2. ``CommonParser``: read the document's ``type``;
3. ``CommonValidator``: run the checks shared by every type;
4. the parser for that type: read the body into its structure;
5. the validator for that type: check that structure.

Steps 2 and 3 run whenever the file loaded. If a parsing step cannot produce
its result, the steps that need it are skipped and the result says the
document was not (fully) validated, so a document is never reported valid
without having been checked.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import load_document
from sks_tool.findings import Finding, ParserFinding
from sks_tool.parsers.base import CommonParser
from sks_tool.validators.base import CommonValidator


@dataclass(frozen=True)
class Result:
    """The outcome of checking one document."""

    doc_type: str | None
    """The document's type, or ``None`` if it could not be determined."""
    findings: list[Finding]
    validated: bool
    """Whether the document was read far enough for every validator to run."""

    @property
    def ok(self) -> bool:
        return self.validated and not self.findings


def _require_findings(step: str, path: Path, findings: Sequence[ParserFinding]) -> None:
    """Stop if a parsing step failed without saying why: that is a bug in sks-tool."""
    if not findings:
        raise RuntimeError(
            f"internal error in sks-tool: {step} could not read {path} but reported no finding; please report this bug"
        )


def check_file(path: Path) -> Result:
    """Parse, then validate, the document at ``path``."""
    document, load_findings = load_document(path)
    findings: list[Finding] = list(load_findings)
    if document is None:
        _require_findings("load_document", path, load_findings)
        return Result(doc_type=None, findings=findings, validated=False)

    doc_type, type_findings = CommonParser(DOC_TYPES).parse(document)
    findings += type_findings
    # The shared checks only need the loaded document, so they run even when
    # the type is unusable: the reader gets every finding available in one pass.
    findings += CommonValidator().validate(document)
    if doc_type is None:
        _require_findings("CommonParser", path, type_findings)
        return Result(doc_type=None, findings=findings, validated=False)

    structure, body_findings = doc_type.parser.parse(document)
    findings += body_findings
    if structure is None:
        _require_findings(type(doc_type.parser).__name__, path, body_findings)
        return Result(doc_type=doc_type.name, findings=findings, validated=False)

    findings += doc_type.validator.validate(structure)
    return Result(doc_type=doc_type.name, findings=findings, validated=True)
