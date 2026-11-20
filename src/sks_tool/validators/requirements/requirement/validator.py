"""The validator for one requirement.

On top of the checks shared with specs (``sks_tool.validators.req_spec_shared``):

- the type is one of the ``RequirementType`` values: ``Business``,
  ``Functional`` or ``Non-functional``;
- the statement contains the word "shall" exactly once, written in bold and
  lowercase (``**shall**``), and states what the system must do, not what it
  must not do: "shall" is not followed by "not";
- the statement is at most 100 characters long, counted as it renders: the
  ``**`` around "shall" do not count;
- the rationale is optional.

The ID has no whitespace or parentheses; its uniqueness is checked across
documents by ``sks_tool.validators.project``.
"""

import re

from sks_tool.docs.req_spec_shared import STATUS_LABEL, TYPE_LABEL, Status
from sks_tool.docs.requirements.requirement.block import Requirement, RequirementType
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.req_spec_shared import (
    check_criteria,
    check_id,
    check_rationale,
    check_sentence,
    check_value,
)

STATEMENT_MAX_CHARACTERS = 100
SHALL = "**shall**"

_SHALL_WORD = re.compile(r"(?<![A-Za-z])shall(?![A-Za-z])", re.IGNORECASE)
# "shall not", "**shall** not" or "**shall not**".
_SHALL_NOT = re.compile(r"(?<![A-Za-z])shall(?:\*\*)?\s+not(?![A-Za-z])", re.IGNORECASE)


class RequirementValidator:
    """Checks a ``Requirement``."""

    def validate(self, requirement: Requirement) -> list[ValidatorFinding]:
        """Return the rules the requirement breaks."""
        entry = f"requirement {requirement.id}"
        return [
            *check_id(requirement.id, entry, requirement.line),
            *check_value(
                "requirement", TYPE_LABEL, requirement.type, list(RequirementType), (entry, "type"), requirement.type_line
            ),
            *check_value(
                "requirement", STATUS_LABEL, requirement.status, list(Status), (entry, "status"), requirement.status_line
            ),
            *self._check_statement(requirement, entry),
            *check_rationale(requirement.rationale, (entry, "rationale"), requirement.rationale_line),
            *check_criteria(requirement.status, requirement.criteria, entry, requirement.status_line),
        ]

    def _check_statement(self, requirement: Requirement, entry: str) -> list[ValidatorFinding]:
        location = (entry, "statement")
        text = " ".join(requirement.statement.split("\n"))
        findings = check_sentence(
            requirement.statement,
            location,
            requirement.statement_line,
            STATEMENT_MAX_CHARACTERS,
            length=len(text.replace(SHALL, "shall")),
        )

        def finding(code: str, message: str, hint: str) -> None:
            findings.append(
                ValidatorFinding(code=code, message=message, hint=hint, location=location, line=requirement.statement_line)
            )

        shalls = list(_SHALL_WORD.finditer(text))
        if not shalls:
            finding(
                "statement-shall-missing",
                "has no 'shall'",
                f"state what is required with {SHALL}, e.g. 'The logger {SHALL} ...'",
            )
        elif len(shalls) > 1:
            finding(
                "statement-shall-repeated",
                f"contains 'shall' {len(shalls)} times",
                "keep one 'shall' per requirement: split it into several requirements",
            )
        if any(not _is_written_as_bold_shall(text, match) for match in shalls):
            finding("statement-shall-not-bold", "'shall' is not written in bold and lowercase", f"write it as {SHALL}")
        if _SHALL_NOT.search(text):
            finding(
                "statement-negative",
                "states what the system must not do ('shall not')",
                "state what the system must do instead, e.g. 'shall write each log to a new file' "
                "rather than 'shall not overwrite a log file'",
            )
        return findings


def _is_written_as_bold_shall(text: str, match: re.Match[str]) -> bool:
    start, end = match.span()
    if text[max(start - 2, 0) : end + 2] == SHALL:
        return True
    # "**shall not**" is bold too: it is reported as a negative statement
    # instead, since writing it "**shall** not" would not fix it.
    return re.match(r"\*\*shall\s+not\*\*", text[max(start - 2, 0) :]) is not None
