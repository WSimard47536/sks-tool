"""The parser for one requirement block.

``RequirementsParser`` splits the document into blocks, each starting at a
level-2 heading, and hands each one to ``RequirementParser``. A block holds,
in order:

1. the type line, the first text after the heading: ``Type: <type>``,
   followed by a blank line;
2. the statement: the next paragraph;
3. optional fields, one bullet per line: ``- Rationale: <text>``.

Blank lines separate paragraphs; comments have already been replaced by blank
lines. Problems this parser can work around (a missing type line, an unknown
field, stray text) are reported and the requirement is kept; a block without
an ID or a statement cannot be read and is dropped. The type's value is kept
as written: whether it is a known type is checked by the validator.
"""

import re
from collections.abc import Sequence

from sks_tool.docs.requirements.requirement.block import FIELDS, TYPE_LABEL, Requirement, RequirementType
from sks_tool.findings import ParserFinding
from sks_tool.parsers.markdown import Line

_FIELD = re.compile(r"-\s+(?P<label>[^:]*):(?P<value>.*)")
_TYPE_LINE = re.compile(rf"{TYPE_LABEL}:(?P<value>.*)")


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
        type_line: Line | None = None
        statement: list[Line] = []
        fields: dict[str, Line] = {}
        # "before" the statement, "in" it, or "after" it (in the fields).
        state = "before"
        previous_kind = "blank"
        seen_text = False
        for number, text in lines:
            if not seen_text and text.strip():
                # The first text under the heading is the type line.
                seen_text = True
                type_match = _TYPE_LINE.fullmatch(text.strip())
                if type_match is not None:
                    type_line = (number, type_match["value"].strip())
                    previous_kind = "type"
                    continue
                findings.append(
                    ParserFinding(
                        code="requirement-type-missing",
                        message=f"{name} does not start with its type",
                        hint=f"write '{TYPE_LABEL}: <type>' as the first line under the heading, with one of: "
                        f"{', '.join(RequirementType)}",
                        line=number,
                    )
                )

            if not text.strip():
                if state == "in":
                    state = "after"
                previous_kind = "blank"
                continue

            if previous_kind == "type":
                # Without a blank line, Markdown renders the type line and what
                # follows as one paragraph. What follows is still read.
                findings.append(
                    ParserFinding(
                        code="requirement-type-not-separated",
                        message=f"no blank line after the type line of {name}",
                        hint="leave a blank line after the type line, so it renders apart from the statement",
                        line=number,
                    )
                )

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
                        hint="a requirement has its type line, one statement paragraph, then its fields as "
                        "'- Rationale: ...'; "
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
                    hint="write the statement as the paragraph under the type line, before any field",
                    line=heading_line,
                )
            )
            return None, findings

        rationale = fields.get("Rationale")
        requirement = Requirement(
            id=requirement_id,
            type=None if type_line is None else type_line[1],
            statement="\n".join(text for _, text in statement),
            rationale=None if rationale is None else rationale[1],
            line=heading_line,
            type_line=None if type_line is None else type_line[0],
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
