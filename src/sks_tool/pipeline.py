"""The pipeline that checks documents: parse them, then validate them.

``check_file`` checks one document. It runs, in order:

1. ``load_document``: split the file into front matter and body;
2. ``CommonParser``: read the front matter keys shared by every document;
3. ``CommonValidator``: check them;
4. the parser for the document's type: read the body into its structure;
5. the validator for that type: check that structure.

Steps 2 and 3 run whenever the file loaded. Steps 4 and 5 need a usable
``type``, and step 5 needs the structure from step 4. When a step cannot
run, the result says the document was not (fully) validated, so a document
is never reported valid without having been checked.

``check_project`` checks every document of a project with ``check_file``,
then runs ``ProjectValidator`` for the rules that span documents.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import load_document
from sks_tool.findings import Finding, ParserFinding, ValidatorFinding
from sks_tool.parsers.base import CommonParser
from sks_tool.validators.base import CommonValidator
from sks_tool.validators.project import ProjectValidator


@dataclass(frozen=True)
class Result:
    """The outcome of checking one document."""

    doc_type: str | None
    """The document's type, or ``None`` if it could not be determined."""
    findings: list[Finding]
    validated: bool
    """Whether the document was read far enough for every validator to run."""
    structure: object | None = None
    """The structure the document was read into, or ``None`` if it could not be."""

    @property
    def ok(self) -> bool:
        return self.validated and not self.findings


def _require_findings(step: str, path: Path, findings: Sequence[ParserFinding]) -> None:
    """Stop if a parsing step failed without saying why: that is a bug in sks-tool."""
    if not findings:
        raise RuntimeError(
            f"internal error in sks-tool: {step} could not read {path} but reported no finding; please report this bug"
        )


def _in_reading_order(findings: Sequence[Finding]) -> list[Finding]:
    """Sort findings by line, so they read top to bottom like the file.

    Findings without a line concern the whole file or its front matter, so
    they come first. The sort is stable: on the same line, findings keep the
    order of the steps that found them, parsing before validation.
    """

    def key(finding: Finding) -> tuple[int, int]:
        line = finding.line if isinstance(finding, ParserFinding | ValidatorFinding) else None
        return (0, 0) if line is None else (1, line)

    return sorted(findings, key=key)


def check_file(path: Path) -> Result:
    """Parse, then validate, the document at ``path``; its findings are in reading order."""
    result = _check_file_step_by_step(path)
    return replace(result, findings=_in_reading_order(result.findings))


def _check_file_step_by_step(path: Path) -> Result:
    document, load_findings = load_document(path)
    findings: list[Finding] = list(load_findings)
    if document is None:
        _require_findings("load_document", path, load_findings)
        return Result(doc_type=None, findings=findings, validated=False)

    metadata, metadata_findings = CommonParser(DOC_TYPES).parse(document)
    findings += metadata_findings
    findings += CommonValidator().validate(metadata)
    if metadata.doc_type is None:
        _require_findings("CommonParser", path, metadata_findings)
        return Result(doc_type=None, findings=findings, validated=False)

    doc_type = DOC_TYPES[metadata.doc_type]
    structure, body_findings = doc_type.parser.parse(document, metadata)
    findings += body_findings
    if structure is None:
        _require_findings(type(doc_type.parser).__name__, path, body_findings)
        return Result(doc_type=doc_type.name, findings=findings, validated=False)

    findings += doc_type.validator.validate(structure)
    return Result(doc_type=doc_type.name, findings=findings, validated=True, structure=structure)


def check_project(documents: Mapping[str, Path]) -> dict[str, Result]:
    """Check every document, then the rules that span documents.

    ``documents`` maps each document's name, as shown in the output, to its
    path. The results are keyed the same way, and each one's findings are in
    reading order.
    """
    results = {name: check_file(path) for name, path in documents.items()}
    structures = {name: result.structure for name, result in results.items() if result.structure is not None}
    for name, project_findings in ProjectValidator().validate(structures).items():
        result = results[name]
        results[name] = replace(result, findings=_in_reading_order([*result.findings, *project_findings]))
    return results
