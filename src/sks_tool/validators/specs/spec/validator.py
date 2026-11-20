"""The validator for one spec.

On top of the checks shared with requirements
(``sks_tool.validators.req_spec_shared``):

- the type is one of the ``SpecType`` values: ``Functional`` or
  ``Non-functional``; specs have no business type;
- the statement is a decision, at most 200 characters long; it has no rule
  about "shall";
- the diagram, if any, follows the diagram rules of
  ``sks_tool.validators.diagram`` and its file is named after the spec's ID:
  ``<ID>.drawio.svg``.

The ID has no whitespace or parentheses; its uniqueness is checked across
documents by ``sks_tool.validators.project``.
"""

from pathlib import Path

from sks_tool.docs.diagram import DIAGRAM_SUFFIX
from sks_tool.docs.req_spec_shared import STATUS_LABEL, TYPE_LABEL, Status
from sks_tool.docs.requirements.requirement.block import RequirementType
from sks_tool.docs.specs.spec.block import Spec, SpecType
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.diagram import check_diagram
from sks_tool.validators.req_spec_shared import (
    check_criteria,
    check_id,
    check_rationale,
    check_sentence,
    check_value,
)

STATEMENT_MAX_CHARACTERS = 200


class SpecValidator:
    """Checks a ``Spec`` of the document in ``folder``, the folder its diagram path is relative to."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def validate(self, spec: Spec) -> list[ValidatorFinding]:
        """Return the rules the spec breaks."""
        entry = f"spec {spec.id}"
        business_hint = (
            "; a business requirement belongs in a requirements document" if spec.type == RequirementType.BUSINESS else ""
        )
        findings = [
            *check_id(spec.id, entry, spec.line),
            *check_value("spec", TYPE_LABEL, spec.type, list(SpecType), (entry, "type"), spec.type_line, business_hint),
            *check_value("spec", STATUS_LABEL, spec.status, list(Status), (entry, "status"), spec.status_line),
            *check_sentence(spec.statement, (entry, "statement"), spec.statement_line, STATEMENT_MAX_CHARACTERS),
            *check_rationale(spec.rationale, (entry, "rationale"), spec.rationale_line),
            *check_criteria(spec.status, spec.criteria, entry, spec.status_line),
        ]
        if spec.diagram is not None:
            findings += check_diagram(
                spec.diagram, self._folder, (entry, "diagram"), expected_name=f"{spec.id}{DIAGRAM_SUFFIX}"
            )
        return findings
