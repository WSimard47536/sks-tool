"""Checks shared by requirements and specs.

- The ID has no whitespace or parentheses.
- The type and the status are among their known values, written exactly.
- The statement fits on one line and is one sentence: it ends with '.', and
  no '.', '!' or '?' followed by a space appears before that.
- The rationale, when present, is not empty and is at most 200 characters.
- Each acceptance criterion is not empty and is at most 200 characters, and
  the checkboxes agree with the status: ``Fulfilled`` needs every box checked,
  any other status at least one unchecked, and ``Pending`` none checked.
"""

import re
from collections.abc import Sequence

from sks_tool.docs.req_spec_shared import STATUS_LABEL, AcceptanceCriterion, Status
from sks_tool.findings import ValidatorFinding

RATIONALE_MAX_CHARACTERS = 200
CRITERION_MAX_CHARACTERS = 200

_SENTENCE_END = re.compile(r"[.!?]\s")
_WHITESPACE = re.compile(r"\s")
_PARENS = re.compile(r"[()]")


def check_value(
    kind: str,
    label: str,
    value: str | None,
    known: Sequence[str],
    location: tuple[str, ...],
    line: int | None,
    extra_hint: str = "",
) -> list[ValidatorFinding]:
    """Check a type or status value; ``None`` means the line was missing, already reported by the parser."""
    if value is None or value in known:
        return []
    return [
        ValidatorFinding(
            code=f"{kind}-{label.lower()}-unknown",
            message=f"'{value}' is not a {kind} {label.lower()}" if value else "is empty",
            hint=f"write '{label}: <{label.lower()}>' with one of: {', '.join(known)} (capitalised, exact){extra_hint}",
            location=location,
            line=line,
        )
    ]


def check_sentence(
    statement: str, location: tuple[str, ...], line: int, max_characters: int, length: int | None = None
) -> list[ValidatorFinding]:
    """Check that a statement is one sentence on one line, at most ``max_characters`` long.

    ``length`` is the length to compare, when it is not the length as
    written (a requirement does not count the ``**`` around "shall").
    """
    findings: list[ValidatorFinding] = []

    def finding(code: str, message: str, hint: str) -> None:
        findings.append(ValidatorFinding(code=code, message=message, hint=hint, location=location, line=line))

    line_count = statement.count("\n") + 1
    if line_count > 1:
        finding("statement-not-one-line", f"spans {line_count} lines", "write the statement on a single line")
    text = " ".join(statement.split("\n"))
    if not text.endswith("."):
        finding("statement-no-final-period", "does not end with '.'", "end the sentence with a period")
    if _SENTENCE_END.search(text):
        finding(
            "statement-several-sentences",
            "contains more than one sentence",
            "keep one sentence per statement: split it into several entries, and write abbreviations such as 'e.g.' in full",
        )
    measured = len(text) if length is None else length
    if measured > max_characters:
        finding(
            "statement-too-long",
            f"is {measured} characters long; the limit is {max_characters}",
            "shorten it, or split it into several entries",
        )
    return findings


def check_rationale(rationale: str | None, location: tuple[str, ...], line: int | None) -> list[ValidatorFinding]:
    """Check a rationale; ``None`` means the field is absent."""
    if rationale is None:
        return []

    def finding(code: str, message: str, hint: str) -> list[ValidatorFinding]:
        return [ValidatorFinding(code=code, message=message, hint=hint, location=location, line=line)]

    if not rationale.strip():
        return finding("rationale-empty", "is empty", "state the reason, or remove the field if it is optional")
    if len(rationale) > RATIONALE_MAX_CHARACTERS:
        return finding(
            "rationale-too-long",
            f"is {len(rationale)} characters long; the limit is {RATIONALE_MAX_CHARACTERS}",
            "shorten it to the key reason",
        )
    return []


def check_criteria(
    status: str | None,
    criteria: Sequence[AcceptanceCriterion],
    entry: str,
    status_line: int | None,
) -> list[ValidatorFinding]:
    """Check each criterion, then that the checkboxes agree with the status.

    ``entry`` names the requirement or spec in locations. A missing list has
    already been reported by the parser; an unknown status is reported by
    ``check_value`` and is not compared with the checkboxes.
    """
    findings: list[ValidatorFinding] = []
    for criterion in criteria:
        location = (entry, "acceptance criteria")
        if not criterion.text:
            findings.append(
                ValidatorFinding(
                    code="criterion-empty",
                    message="a criterion is empty",
                    hint="state what must be true for it to be met, or remove the checkbox",
                    location=location,
                    line=criterion.line,
                )
            )
        elif len(criterion.text) > CRITERION_MAX_CHARACTERS:
            findings.append(
                ValidatorFinding(
                    code="criterion-too-long",
                    message=f"a criterion is {len(criterion.text)} characters long; the limit is {CRITERION_MAX_CHARACTERS}",
                    hint="shorten it, or split it into several criteria",
                    location=location,
                    line=criterion.line,
                )
            )

    if not criteria or status not in set(Status):
        return findings
    checked = sum(criterion.checked for criterion in criteria)
    unchecked = len(criteria) - checked
    location = (entry, "status")

    def mismatch(code: str, message: str, hint: str) -> None:
        findings.append(ValidatorFinding(code=code, message=message, hint=hint, location=location, line=status_line))

    if status == Status.FULFILLED and unchecked:
        mismatch(
            "status-fulfilled-unchecked",
            f"is {Status.FULFILLED} but {_criteria(unchecked)} unchecked",
            f"check the criteria that are met, or set '{STATUS_LABEL}:' to the status the work is at",
        )
    elif status == Status.PENDING and checked:
        mismatch(
            "status-pending-checked",
            f"is {Status.PENDING} but {_criteria(checked)} checked",
            f"set '{STATUS_LABEL}: {Status.UNDERWAY}' if work has started, or uncheck them",
        )
    elif status != Status.FULFILLED and not unchecked:
        mismatch(
            "status-all-checked",
            f"is {status} but every criterion is checked",
            f"set '{STATUS_LABEL}: {Status.FULFILLED}', or add the criteria that are still to be met",
        )
    return findings


def _criteria(count: int) -> str:
    """'1 criterion is' or 'N criteria are', for messages."""
    return "1 criterion is" if count == 1 else f"{count} criteria are"


def check_id(entry_id: str, entry: str, line: int) -> list[ValidatorFinding]:
    """Check that an ID has no whitespace or parentheses: it names files (a spec's diagram) and links."""
    forbidden = [
        what
        for what, found in (("whitespace", _WHITESPACE.search(entry_id)), ("parentheses", _PARENS.search(entry_id)))
        if found
    ]
    if not forbidden:
        return []
    return [
        ValidatorFinding(
            code="id-invalid",
            message=f"the ID contains {' and '.join(forbidden)}",
            hint="write the ID without spaces or parentheses, e.g. 'LOG-001'; it is used in file names and links",
            location=(entry,),
            line=line,
        )
    ]
