"""Reading the blocks shared by requirements and specs.

A block holds, in order (see ``sks_tool.docs.req_spec_shared``):

1. the type line, ``Type: <type>``, followed by a blank line;
2. the status line, ``Status: <status>``, followed by a blank line;
3. the statement: the next paragraph;
4. optional fields, one bullet per line: ``- Rationale: <text>``;
5. after a blank line, the line ``Acceptance criteria:`` and a checkbox
   list, one criterion per line: ``- [ ] <criterion>``, or
   ``- [x] <criterion>`` once it is met;
6. for a spec only, after a blank line, an optional diagram image.

The blank lines are required so each part renders as its own paragraph.

Blank lines separate paragraphs; comments have already been replaced by
blank lines. Problems the parser can work around (a missing type or status
line, an unknown field, stray text) are reported and the block is still
read; a block without a statement cannot be read. Values are kept as
written: whether a type or a status is known is checked by the validators.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from sks_tool.docs.diagram import Diagram
from sks_tool.docs.req_spec_shared import CRITERIA_LABEL, STATUS_LABEL, TYPE_LABEL, AcceptanceCriterion, Status
from sks_tool.findings import ParserFinding
from sks_tool.parsers.diagram import read_image
from sks_tool.parsers.markdown import Line

_FIELD = re.compile(r"-\s+(?P<label>[^:]*):(?P<value>.*)")
_CRITERION = re.compile(r"-\s+\[(?P<mark>[ xX])\](?:\s+(?P<text>.*))?")
_LABEL_LINES = (
    ("type", TYPE_LABEL, re.compile(rf"{TYPE_LABEL}:(?P<value>.*)")),
    ("status", STATUS_LABEL, re.compile(rf"{STATUS_LABEL}:(?P<value>.*)")),
)


@dataclass
class TrackedBlock:
    """What was read from a requirement or spec block, before it becomes a ``Requirement`` or ``Spec``."""

    type: Line | None = None
    status: Line | None = None
    statement: list[Line] = field(default_factory=list)
    fields: dict[str, Line] = field(default_factory=dict)
    criteria: list[AcceptanceCriterion] = field(default_factory=list)
    criteria_line: int | None = None
    diagram: Diagram | None = None

    def statement_text(self) -> str:
        """The statement as written; lines are joined with ``\\n`` if it spans several."""
        return "\n".join(text for _, text in self.statement)


def read_tracked_block(
    kind: str,
    heading: Line,
    lines: Sequence[Line],
    *,
    fields: Sequence[str],
    labels: Sequence[str],
    diagram: bool,
) -> tuple[TrackedBlock | None, list[ParserFinding]]:
    """Read one requirement or spec block; return ``None`` if it has no statement.

    ``kind`` names the entry in finding codes and messages (``requirement``,
    ``spec``), ``fields`` are the fields it may have, ``labels`` the values
    its type may take (for hints), and ``diagram`` whether it may end with a
    diagram.
    """
    heading_line, entry_id = heading
    name = f"{kind} {entry_id}"
    findings: list[ParserFinding] = []
    block = TrackedBlock()
    pending_labels = list(_LABEL_LINES)
    # Where the reading is: the "statement", the "fields", the "criteria" or the "diagram".
    phase = "statement"
    previous = "blank"
    list_kind = "field"

    def report(code: str, message: str, hint: str, line: int) -> None:
        findings.append(ParserFinding(code=f"{kind}-{code}", message=message, hint=hint, line=line))

    for number, text in lines:
        stripped = text.strip()
        if not stripped:
            if phase == "statement" and block.statement:
                phase = "fields"
            previous = "blank"
            continue

        if previous in ("type", "status"):
            # Without a blank line, Markdown renders the line and what follows
            # as one paragraph. What follows is still read.
            report(
                f"{previous}-not-separated",
                f"no blank line after the {previous} line of {name}",
                f"leave a blank line after the {previous} line, so it renders as its own paragraph",
                number,
            )

        if text[0] in " \t" and previous in ("field", "criterion", "continuation"):
            report(
                f"{list_kind}-continued",
                f"a {'field' if list_kind == 'field' else 'criterion'} of {name} continues on this line",
                "each item must fit on one line: join this line onto the item's line",
                number,
            )
            previous = "continuation"
            continue

        matched_label = False
        while pending_labels:
            label, written, pattern = pending_labels.pop(0)
            match = pattern.fullmatch(stripped)
            if match is not None:
                value = (number, match["value"].strip())
                if label == "type":
                    block.type = value
                else:
                    block.status = value
                previous = label
                matched_label = True
                break
            _report_missing_label(kind, name, label, written, labels, number, findings)
        if matched_label:
            continue

        is_bullet = stripped == "-" or stripped.startswith(("- ", "-\t"))
        # Right under other text, Markdown renders the criteria label as part of
        # the statement or of the last field, and the diagram as part of the
        # last criterion. (A type or status line has been reported already.)
        follows_text = previous not in ("blank", "type", "status")
        if stripped == CRITERIA_LABEL and phase in ("statement", "fields"):
            if follows_text:
                report(
                    "criteria-not-separated",
                    f"no blank line before the acceptance criteria of {name}",
                    f"leave a blank line before '{CRITERIA_LABEL}', so it renders as its own paragraph",
                    number,
                )
            phase = "criteria"
            block.criteria_line = number
            previous = "criteria-label"
            continue
        if is_bullet and phase in ("statement", "fields"):
            phase = "fields"
            _read_field(kind, name, number, stripped, fields, block, findings)
            previous = list_kind = "field"
            continue
        if is_bullet and phase == "criteria":
            _read_criterion(kind, name, number, stripped, block, findings)
            previous = list_kind = "criterion"
            continue
        image = read_image(number, text) if diagram else None
        if image is not None and phase != "statement":
            if block.diagram is not None:
                findings.append(
                    ParserFinding(
                        code="diagram-repeated",
                        message=f"{name} has more than one diagram",
                        hint=f"keep a single diagram; the first one, on line {block.diagram.line}, is used",
                        line=number,
                    )
                )
            else:
                if follows_text:
                    report(
                        "diagram-not-separated",
                        f"no blank line before the diagram of {name}",
                        "leave a blank line before the diagram, so it renders apart from the criteria",
                        number,
                    )
                block.diagram = image
            phase = "diagram"
            previous = "image"
            continue
        if phase == "statement" and not is_bullet:
            block.statement.append((number, stripped))
            previous = "text"
            continue
        if previous != "stray":
            # Only the first line of each stray paragraph is reported.
            report(
                "text-unexpected",
                f"unexpected text in {name}",
                f"a {kind} has its type and status lines, one statement paragraph, its fields as '- Rationale: ...', "
                f"then '{CRITERIA_LABEL}' and its checkboxes{', then its diagram' if diagram else ''}; "
                "remove this text or put it in a <!-- comment -->",
                number,
            )
        previous = "stray"

    # A label line never reached, in a block with nothing after it, is still missing.
    for label, written, _ in pending_labels:
        _report_missing_label(kind, name, label, written, labels, heading_line, findings)
    if block.criteria_line is None or not block.criteria:
        report(
            "criteria-missing",
            f"{name} has no acceptance criteria",
            f"add a '{CRITERIA_LABEL}' line after the fields, then one checkbox per criterion: '- [ ] <criterion>'",
            heading_line if block.criteria_line is None else block.criteria_line,
        )
    if not block.statement:
        report(
            "statement-missing",
            f"{name} has no statement",
            "write the statement as the paragraph under the status line, before any field",
            heading_line,
        )
        return None, findings
    return block, findings


def _report_missing_label(
    kind: str, name: str, label: str, written: str, types: Sequence[str], line: int, findings: list[ParserFinding]
) -> None:
    expected = ", ".join(types) if label == "type" else ", ".join(Status)
    findings.append(
        ParserFinding(
            code=f"{kind}-{label}-missing",
            message=f"{name} has no {label} line here",
            hint=f"write '{written}: <{label}>' {'first' if label == 'type' else 'after the type line'}, "
            f"with one of: {expected}",
            line=line,
        )
    )


def _read_field(
    kind: str,
    name: str,
    number: int,
    stripped: str,
    known_fields: Sequence[str],
    block: TrackedBlock,
    findings: list[ParserFinding],
) -> None:
    known = ", ".join(known_fields)
    match = _FIELD.fullmatch(stripped)
    if match is None or not match["label"].strip():
        findings.append(
            ParserFinding(
                code=f"{kind}-field-malformed",
                message=f"a bullet of {name} is not a field",
                hint=f"write fields as '- <Field>: <value>', with one of: {known}; "
                f"acceptance criteria go after a '{CRITERIA_LABEL}' line",
                line=number,
            )
        )
        return
    label = match["label"].strip()
    if label not in known_fields:
        findings.append(
            ParserFinding(
                code=f"{kind}-field-unknown",
                message=f"{name} has an unknown field '{label}'",
                hint=f"use one of: {known} (capitalised, exact)",
                line=number,
            )
        )
        return
    if label in block.fields:
        findings.append(
            ParserFinding(
                code=f"{kind}-field-repeated",
                message=f"{name} has its '{label}' field more than once",
                hint=f"keep a single '{label}' field; the first one, on line {block.fields[label][0]}, is used",
                line=number,
            )
        )
        return
    block.fields[label] = (number, match["value"].strip())


def _read_criterion(
    kind: str, name: str, number: int, stripped: str, block: TrackedBlock, findings: list[ParserFinding]
) -> None:
    match = _CRITERION.fullmatch(stripped)
    if match is None:
        findings.append(
            ParserFinding(
                code=f"{kind}-criterion-malformed",
                message=f"a bullet of {name}'s acceptance criteria is not a checkbox",
                hint="write each criterion as '- [ ] <criterion>', or '- [x] <criterion>' once it is met",
                line=number,
            )
        )
        return
    block.criteria.append(AcceptanceCriterion(text=(match["text"] or "").strip(), checked=match["mark"] != " ", line=number))
