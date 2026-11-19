"""The validator for one requirement.

The statement must:

- fit on one line and be one sentence: it ends with '.', and no '.', '!' or
  '?' followed by a space appears before that;
- contain the word "shall" exactly once, written in bold and lowercase
  (``**shall**``);
- be at most 100 characters long, counted as it renders: the ``**`` around
  "shall" do not count.

The rationale is optional; when present it must not be empty and must be at
most 200 characters long.

The ID's only rule for now is uniqueness, checked across documents by
``sks_tool.validators.project``.
"""

import re

from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.findings import ValidatorFinding

STATEMENT_MAX_CHARACTERS = 100
RATIONALE_MAX_CHARACTERS = 200
SHALL = "**shall**"

_SHALL_WORD = re.compile(r"(?<![A-Za-z])shall(?![A-Za-z])", re.IGNORECASE)
_SENTENCE_END = re.compile(r"[.!?]\s")


class RequirementValidator:
    """Checks a ``Requirement``."""

    def validate(self, requirement: Requirement) -> list[ValidatorFinding]:
        """Return the rules the requirement breaks."""
        return self._check_statement(requirement) + self._check_rationale(requirement)

    def _check_statement(self, requirement: Requirement) -> list[ValidatorFinding]:
        findings: list[ValidatorFinding] = []
        statement = requirement.statement

        def finding(code: str, message: str, hint: str) -> ValidatorFinding:
            return ValidatorFinding(
                code=code,
                message=message,
                hint=hint,
                location=(f"requirement {requirement.id}", "statement"),
                line=requirement.statement_line,
            )

        line_count = statement.count("\n") + 1
        if line_count > 1:
            findings.append(
                finding(
                    "statement-not-one-line",
                    f"spans {line_count} lines",
                    "write the statement on a single line",
                )
            )
        text = " ".join(statement.split("\n"))

        if not text.endswith("."):
            findings.append(finding("statement-no-final-period", "does not end with '.'", "end the sentence with a period"))
        if _SENTENCE_END.search(text):
            findings.append(
                finding(
                    "statement-several-sentences",
                    "contains more than one sentence",
                    "keep one sentence per requirement: split it into several requirements, "
                    "and write abbreviations such as 'e.g.' in full",
                )
            )

        shalls = list(_SHALL_WORD.finditer(text))
        if not shalls:
            findings.append(
                finding(
                    "statement-shall-missing",
                    "has no 'shall'",
                    f"state what is required with {SHALL}, e.g. 'The logger {SHALL} ...'",
                )
            )
        elif len(shalls) > 1:
            findings.append(
                finding(
                    "statement-shall-repeated",
                    f"contains 'shall' {len(shalls)} times",
                    "keep one 'shall' per requirement: split it into several requirements",
                )
            )
        if any(not _is_written_as_bold_shall(text, match) for match in shalls):
            findings.append(
                finding(
                    "statement-shall-not-bold",
                    "'shall' is not written in bold and lowercase",
                    f"write it as {SHALL}",
                )
            )

        rendered_length = len(text.replace(SHALL, "shall"))
        if rendered_length > STATEMENT_MAX_CHARACTERS:
            findings.append(
                finding(
                    "statement-too-long",
                    f"is {rendered_length} characters long; the limit is {STATEMENT_MAX_CHARACTERS}",
                    "shorten it, or split it into several requirements",
                )
            )
        return findings

    def _check_rationale(self, requirement: Requirement) -> list[ValidatorFinding]:
        rationale = requirement.rationale
        if rationale is None:
            return []

        def finding(code: str, message: str, hint: str) -> ValidatorFinding:
            return ValidatorFinding(
                code=code,
                message=message,
                hint=hint,
                location=(f"requirement {requirement.id}", "rationale"),
                line=requirement.rationale_line,
            )

        if not rationale.strip():
            return [finding("rationale-empty", "is empty", "state why the requirement exists, or remove the field")]
        if len(rationale) > RATIONALE_MAX_CHARACTERS:
            return [
                finding(
                    "rationale-too-long",
                    f"is {len(rationale)} characters long; the limit is {RATIONALE_MAX_CHARACTERS}",
                    "shorten it to the key reason",
                )
            ]
        return []


def _is_written_as_bold_shall(text: str, match: re.Match[str]) -> bool:
    start, end = match.span()
    return text[max(start - 2, 0) : end + 2] == SHALL
