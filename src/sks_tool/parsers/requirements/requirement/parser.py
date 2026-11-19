"""The parser for one requirement block.

``RequirementsParser`` splits the document into blocks, each starting at a
level-2 heading, and hands each one to ``RequirementParser``. A block holds,
in order:

1. the statement: the first paragraph after the heading;
2. optional fields, one bullet per line: ``- Rationale: <text>``.

Blank lines separate paragraphs; comments have already been replaced by blank
lines. Problems this parser can work around (an unknown field, stray text) are
reported and the requirement is kept; a block without an ID or a statement
cannot be read and is dropped.
"""

import re
from collections.abc import Sequence

from sks_tool.docs.requirements.requirement.block import FIELDS, Requirement
from sks_tool.findings import ParserFinding

type Line = tuple[int, str]
"""A line of the file: its 1-based number and its text."""

_FIELD = re.compile(r"-\s+(?P<label>[^:]*):(?P<value>.*)")


class RequirementParser:
    """Reads one requirement block into a ``Requirement``."""

    def parse(self, heading: Line, lines: Sequence[Line]) -> tuple[Requirement | None, list[ParserFinding]]:
        """Return the requirement, or ``None`` plus the findings that prevented reading it.

        ``heading`` is the block's heading line, already stripped of its
        ``##`` marker; ``lines`` are the lines up to the next heading.
        """
        heading_line, requirement_id = heading
        if not requirement_id:
            return None, [
                ParserFinding(
                    code="requirement-id-missing",
                    message="a requirement heading has no ID",
                    hint="write the requirement's ID after '## '",
                    line=heading_line,
                )
            ]

        findings: list[ParserFinding] = []
        name = f"requirement {requirement_id}"
        statement: list[Line] = []
        fields: dict[str, Line] = {}
        # "before" the statement, "in" it, or "after" it (in the fields).
        state = "before"
        previous_kind = "blank"
        for number, text in lines:
            if not text.strip():
                if state == "in":
                    state = "after"
                previous_kind = "blank"
                continue

            if text[0] in " \t" and previous_kind in ("field", "continuation"):
                findings.append(
                    ParserFinding(
                        code="requirement-field-continued",
                        message=f"a field of {name} continues on this line",
                        hint="a field must fit on one line: join this line onto the field's line",
                        line=number,
                    )
                )
                previous_kind = "continuation"
                continue

            stripped = text.strip()
            if stripped == "-" or stripped.startswith(("- ", "-\t")):
                state = "after"
                self._parse_field(name, number, stripped, fields, findings)
                previous_kind = "field"
                continue

            if state == "before":
                state = "in"
            if state == "in":
                statement.append((number, stripped))
            elif previous_kind != "text":
                # Only the first line of each stray paragraph is reported.
                findings.append(
                    ParserFinding(
                        code="requirement-text-unexpected",
                        message=f"unexpected text in {name}",
                        hint="a requirement has one statement paragraph, then its fields as '- Rationale: ...'; "
                        "remove this text or put it in a <!-- comment -->",
                        line=number,
                    )
                )
            previous_kind = "text"

        if not statement:
            findings.append(
                ParserFinding(
                    code="requirement-statement-missing",
                    message=f"{name} has no statement",
                    hint="write the statement as the paragraph right under the heading, before any field",
                    line=heading_line,
                )
            )
            return None, findings

        rationale = fields.get("Rationale")
        requirement = Requirement(
            id=requirement_id,
            statement="\n".join(text for _, text in statement),
            rationale=None if rationale is None else rationale[1],
            line=heading_line,
            statement_line=statement[0][0],
            rationale_line=None if rationale is None else rationale[0],
        )
        return requirement, findings

    @staticmethod
    def _parse_field(name: str, number: int, stripped: str, fields: dict[str, Line], findings: list[ParserFinding]) -> None:
        known = ", ".join(FIELDS)
        match = _FIELD.fullmatch(stripped)
        if match is None or not match["label"].strip():
            findings.append(
                ParserFinding(
                    code="requirement-field-malformed",
                    message=f"a bullet of {name} is not a field",
                    hint=f"write fields as '- <Field>: <value>', with one of: {known}",
                    line=number,
                )
            )
            return
        label = match["label"].strip()
        if label not in FIELDS:
            findings.append(
                ParserFinding(
                    code="requirement-field-unknown",
                    message=f"{name} has an unknown field '{label}'",
                    hint=f"use one of: {known} (capitalised, exact)",
                    line=number,
                )
            )
            return
        if label in fields:
            findings.append(
                ParserFinding(
                    code="requirement-field-repeated",
                    message=f"{name} has its '{label}' field more than once",
                    hint=f"keep a single '{label}' field; the first one, on line {fields[label][0]}, is used",
                    line=number,
                )
            )
            return
        fields[label] = (number, match["value"].strip())
