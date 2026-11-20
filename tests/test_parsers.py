from pathlib import Path

import pytest

from sks_tool.docs.base import Metadata
from sks_tool.docs.diagram import Diagram
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.docs.glossary.term.block import Term
from sks_tool.docs.overview.doc import OverviewDoc, TextSection
from sks_tool.docs.req_spec_shared import AcceptanceCriterion
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.docs.specs.doc import SpecsDoc
from sks_tool.docs.specs.spec.block import Spec
from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document, load_document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.base import CommonParser
from sks_tool.parsers.glossary.parser import GlossaryParser
from sks_tool.parsers.overview.parser import OverviewParser
from sks_tool.parsers.requirements.parser import RequirementsParser
from sks_tool.parsers.specs.parser import SpecsParser

FULL = {"title": "A title", "description": "A description."}
METADATA = Metadata(doc_type="requirements", title="A title", description="A description.")


def make_document(front_matter: dict[str, object], body: str = "", body_line: int = 6) -> Document:
    return Document(path=Path("doc.md"), front_matter=front_matter, body=body, body_line=body_line)


def test_document_is_split_into_front_matter_and_body(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_bytes(b"---\ntype: glossary\nextra: 1\n---\n\n# Heading\n")
    document, findings = load_document(path)
    assert findings == []
    assert document is not None
    assert document.front_matter == {"type": "glossary", "extra": 1}
    assert document.body == "\n# Heading\n"
    assert document.body_line == 5


def test_load_document_failures_are_parser_findings(tmp_path: Path) -> None:
    document, findings = load_document(tmp_path / "absent.md")
    assert document is None
    assert [type(finding) for finding in findings] == [ParserFinding]


# --- CommonParser -------------------------------------------------------------


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_common_parser_reads_the_metadata(name: str) -> None:
    metadata, findings = CommonParser(DOC_TYPES).parse(make_document({"type": name, **FULL}))
    assert findings == []
    assert metadata == Metadata(doc_type=name, title="A title", description="A description.")


@pytest.mark.parametrize(
    ("front_matter", "code"),
    [
        (FULL, "type-missing"),
        ({"type": 3, **FULL}, "type-not-text"),
        ({"type": "recipe", **FULL}, "type-unknown"),
    ],
)
def test_common_parser_reports_an_unusable_type(front_matter: dict[str, object], code: str) -> None:
    metadata, findings = CommonParser(DOC_TYPES).parse(make_document(front_matter))
    assert metadata.doc_type is None
    assert [finding.code for finding in findings] == [code]


@pytest.mark.parametrize("key", ["title", "description"])
def test_common_parser_reports_missing_or_unusable_text_keys(key: str) -> None:
    without = {name: value for name, value in FULL.items() if name != key}
    metadata, findings = CommonParser(DOC_TYPES).parse(make_document({"type": "glossary", **without}))
    assert getattr(metadata, key) is None
    assert metadata.doc_type == "glossary"
    assert [finding.code for finding in findings] == [f"{key}-missing"]

    _, findings = CommonParser(DOC_TYPES).parse(make_document({"type": "glossary", **FULL, key: 2024}))
    assert [finding.code for finding in findings] == [f"{key}-not-text"]


@pytest.mark.parametrize("key", ["title", "description"])
def test_a_blank_text_key_is_read_as_empty_for_the_validator(key: str) -> None:
    """YAML reads 'title:' with no value as null; that is an empty title, not a non-text one."""
    metadata, findings = CommonParser(DOC_TYPES).parse(make_document({"type": "glossary", **FULL, key: None}))
    assert findings == []
    assert getattr(metadata, key) == ""


def test_common_parser_hint_lists_the_known_types() -> None:
    _, findings = CommonParser(DOC_TYPES).parse(make_document({"type": "recipe", **FULL}))
    assert all(name in findings[0].hint for name in DOC_TYPES)


# --- RequirementsParser and SpecsParser ---------------------------------------


def parse_requirements(body: str) -> tuple[RequirementsDoc, list[tuple[str, int | None]]]:
    """Parse ``body`` as if it started on line 6; return the structure and (code, line) of each finding."""
    doc, findings = RequirementsParser().parse(make_document({}, body=body), METADATA)
    assert doc is not None
    return doc, [(finding.code, finding.line) for finding in findings]


def parse_specs(body: str) -> tuple[SpecsDoc, list[tuple[str, int | None]]]:
    """Parse ``body`` as if it started on line 6; return the structure and (code, line) of each finding."""
    doc, findings = SpecsParser().parse(make_document({}, body=body), SPECS_METADATA)
    assert doc is not None
    return doc, [(finding.code, finding.line) for finding in findings]


def parse_entries(kind: str, body: str) -> tuple[int, list[tuple[str, int | None]]]:
    """Parse ``body`` as a requirements or specs document; return how many entries were read, and the findings."""
    if kind == "requirement":
        requirements, findings = parse_requirements(body)
        return len(requirements.requirements), findings
    specs, findings = parse_specs(body)
    return len(specs.specs), findings


SPECS_METADATA = Metadata(doc_type="specs", title="A title", description="A description.")
HEAD = "## A\n\nType: Functional\n\nStatus: Pending\n\n"
"""An entry's heading (line 6), type line (8) and status line (10); its statement then starts on line 12."""
BODY = "The logger **shall** log.\n\n- Rationale: Why.\n\nAcceptance criteria:\n\n- [ ] It works.\n"
"""Statement (line 12), rationale (14), criteria label (16) and one criterion (18), after ``HEAD``."""


def test_requirements_are_read_with_their_lines() -> None:
    doc, findings = parse_requirements(
        "<!-- guidance -->\n"  # 6
        "\n"  # 7
        "## LOG-001\n"  # 8
        "\n"  # 9
        "Type: Business\n"  # 10
        "\n"  # 11
        "Status: Underway\n"  # 12
        "\n"  # 13
        "The logger **shall** log.\n"  # 14
        "\n"  # 15
        "- Rationale: Because.\n"  # 16
        "\n"  # 17
        "Acceptance criteria:\n"  # 18
        "\n"  # 19
        "- [x] Done.\n"  # 20
        "- [X] Also done.\n"  # 21
        "- [ ] Not yet.\n"  # 22
        "\n"  # 23
        "## LOG-002 ##\n"  # 24
        "Type: Non-functional\n"  # 25: the type line may follow the heading directly
        "\n"  # 26
        "Status: Pending\n"  # 27
        "\n"  # 28
        "The logger **shall** beep.\n"  # 29
        "\n"  # 30
        "Acceptance criteria:\n"  # 31
        "- [ ]\n"  # 32: the list may follow its label directly; an empty criterion is kept for the validator
    )
    assert findings == []
    assert doc.metadata is METADATA
    assert doc.requirements == (
        Requirement(
            id="LOG-001",
            type="Business",
            status="Underway",
            statement="The logger **shall** log.",
            rationale="Because.",
            criteria=(
                AcceptanceCriterion(text="Done.", checked=True, line=20),
                AcceptanceCriterion(text="Also done.", checked=True, line=21),
                AcceptanceCriterion(text="Not yet.", checked=False, line=22),
            ),
            line=8,
            type_line=10,
            status_line=12,
            statement_line=14,
            rationale_line=16,
        ),
        Requirement(
            id="LOG-002",
            type="Non-functional",
            status="Pending",
            statement="The logger **shall** beep.",
            rationale=None,
            criteria=(AcceptanceCriterion(text="", checked=False, line=32),),
            line=24,
            type_line=25,
            status_line=27,
            statement_line=29,
            rationale_line=None,
        ),
    )


def test_specs_are_read_with_their_lines_and_diagram() -> None:
    doc, findings = parse_specs(HEAD + BODY + "\n![Design](A.drawio.svg)\n")
    assert findings == []
    assert doc.metadata is SPECS_METADATA
    assert doc.specs == (
        Spec(
            id="A",
            type="Functional",
            status="Pending",
            statement="The logger **shall** log.",
            rationale="Why.",
            criteria=(AcceptanceCriterion(text="It works.", checked=False, line=18),),
            diagram=Diagram(alt="Design", path="A.drawio.svg", line=20),
            line=6,
            type_line=8,
            status_line=10,
            statement_line=12,
            rationale_line=14,
        ),
    )


def test_a_spec_without_a_diagram_is_read() -> None:
    doc, findings = parse_specs(HEAD + BODY)
    assert findings == []
    assert doc.specs[0].diagram is None


@pytest.mark.parametrize(
    "body",
    [
        "## A\n\nType: Functionnal\n\nStatus: Done\n\n" + BODY,  # kept for the validator
    ],
)
def test_type_and_status_are_kept_as_written_for_the_validator(body: str) -> None:
    doc, findings = parse_requirements(body)
    assert findings == []
    assert (doc.requirements[0].type, doc.requirements[0].status) == ("Functionnal", "Done")


def test_a_statement_over_several_lines_is_kept_whole_for_the_validator() -> None:
    doc, findings = parse_requirements(HEAD + "First line\nsecond line.\n\nAcceptance criteria:\n\n- [ ] x\n")
    assert findings == []
    assert doc.requirements[0].statement == "First line\nsecond line."


def test_an_empty_rationale_is_kept_for_the_validator() -> None:
    doc, findings = parse_requirements(
        HEAD + "The logger **shall** log.\n\n- Rationale:\n\nAcceptance criteria:\n\n- [ ] x\n"
    )
    assert findings == []
    assert doc.requirements[0].rationale == ""


@pytest.mark.parametrize("kind", ["requirement", "spec"])
@pytest.mark.parametrize(
    ("body", "expected", "kept"),
    [
        # Outside entries: only blank lines and comments.
        (f"Intro\nstill intro\n\n{HEAD}{BODY}", [("text-outside-{k}", 6)], 1),
        (f"# Title\n\n{HEAD}{BODY}", [("heading-wrong-level", 6)], 1),
        (f"{HEAD}{BODY}\n### Detail\n", [("heading-wrong-level", 20)], 1),
        (f"{HEAD}{BODY}<!-- never closed\n", [("comment-unterminated", 19)], 1),
        (
            f"{HEAD}The logger **shall** log. <!-- note -->\n\n- Rationale: Why.\n\nAcceptance criteria:\n\n- [ ] x\n",
            [("comment-not-whole-line", 12)],
            1,
        ),
        # The type and status lines.
        (f"## A\n\nStatus: Pending\n\n{BODY}", [("{k}-type-missing", 8)], 1),
        (f"## A\n\nType: Functional\n\n{BODY}", [("{k}-status-missing", 10)], 1),
        (f"## A\n\n{BODY}", [("{k}-type-missing", 8), ("{k}-status-missing", 8)], 1),
        ("## A\n\nType: Functional\nStatus: Pending\n\n" + BODY, [("{k}-type-not-separated", 9)], 1),
        ("## A\n\nType: Functional\n\nStatus: Pending\n" + BODY, [("{k}-status-not-separated", 11)], 1),
        # The labels are exact: 'type:' is not a type line, so it is read as the
        # statement, and what follows it is stray.
        (
            "## A\n\ntype: Functional\n\nStatus: Pending\n\n" + BODY,
            [
                ("{k}-type-missing", 8),
                ("{k}-status-missing", 8),
                ("{k}-text-unexpected", 10),
                ("{k}-text-unexpected", 12),
            ],
            1,
        ),
        # The statement, fields and criteria.
        ("##\n\n" + HEAD.removeprefix("## A\n\n") + BODY, [("{k}-id-missing", 6)], 0),
        (f"{HEAD}- Rationale: Why.\n\nAcceptance criteria:\n\n- [ ] x\n", [("{k}-statement-missing", 6)], 0),
        (f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n", [("{k}-criteria-missing", 6)], 1),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n\nAcceptance criteria:\n",
            [("{k}-criteria-missing", 16)],
            1,
        ),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n- [ ] x\n",
            [("{k}-field-malformed", 15), ("{k}-criteria-missing", 6)],
            1,
        ),
        (f"{HEAD}{BODY}- not a checkbox\n", [("{k}-criterion-malformed", 19)], 1),
        (f"{HEAD}{BODY}  continued\n", [("{k}-criterion-continued", 19)], 1),
        (f"{HEAD}{BODY}\nMore text.\nAnd more.\n", [("{k}-text-unexpected", 20)], 1),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n- Notes: x\n\nAcceptance criteria:\n\n- [ ] x\n",
            [("{k}-field-unknown", 15)],
            1,
        ),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n- Rationale: Again.\n"
            "\nAcceptance criteria:\n\n- [ ] x\n",
            [("{k}-field-repeated", 15)],
            1,
        ),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\n  continued\n\nAcceptance criteria:\n\n- [ ] x\n",
            [("{k}-field-continued", 15)],
            1,
        ),
    ],
)
def test_requirements_and_specs_format_problems_are_parse_findings(
    kind: str, body: str, expected: list[tuple[str, int]], kept: int
) -> None:
    count, findings = parse_entries(kind, body)
    assert findings == [(code.format(k=kind), line) for code, line in expected]
    assert count == kept


def test_a_label_line_never_reached_is_still_reported() -> None:
    _, findings = parse_requirements("## A\n\nType: Functional\n")
    assert ("requirement-status-missing", 6) in findings
    assert ("requirement-statement-missing", 6) in findings


def test_the_first_of_repeated_fields_is_used() -> None:
    doc, _ = parse_requirements(
        f"{HEAD}The logger **shall** log.\n\n- Rationale: x\n- Rationale: y\n\nAcceptance criteria:\n\n- [ ] x\n"
    )
    assert doc.requirements[0].rationale == "x"


def test_a_comment_after_an_id_is_reported_and_kept_out_of_the_id() -> None:
    """Otherwise '## A <!-- draft -->' would not clash with another '## A'."""
    doc, findings = parse_requirements("## A <!-- draft -->\n\nType: Functional\n\nStatus: Pending\n\n" + BODY)
    assert findings == [("comment-not-whole-line", 6)]
    assert doc.requirements[0].id == "A"


def test_a_comment_inside_a_rationale_does_not_count_toward_its_length() -> None:
    doc, findings = parse_requirements(
        f"{HEAD}The logger **shall** log.\n\n- Rationale: Why. <!-- x -->\n\nAcceptance criteria:\n\n- [ ] x\n"
    )
    assert findings == [("comment-not-whole-line", 14)]
    assert doc.requirements[0].rationale == "Why."


def test_a_requirement_has_no_diagram() -> None:
    _, findings = parse_requirements(f"{HEAD}{BODY}\n![Design](A.drawio.svg)\n")
    assert findings == [("requirement-text-unexpected", 20)]


def test_a_spec_needs_a_rationale() -> None:
    doc, findings = parse_specs(f"{HEAD}The logger **shall** log.\n\nAcceptance criteria:\n\n- [ ] x\n")
    assert findings == [("spec-rationale-missing", 12)]
    assert doc.specs[0].rationale is None


@pytest.mark.parametrize(
    ("tail", "expected"),
    [
        ("\n![a](A.drawio.svg)\n![b](B.drawio.svg)\n", [("diagram-repeated", 21)]),
        ("\n![a](A.drawio.svg)\n\nMore text.\n", [("spec-text-unexpected", 22)]),
        ("\n![a](A.drawio.svg)\n- [ ] late\n", [("spec-text-unexpected", 21)]),
    ],
)
def test_a_spec_diagram_comes_last_and_once(tail: str, expected: list[tuple[str, int]]) -> None:
    doc, findings = parse_specs(HEAD + BODY + tail)
    assert findings == expected
    assert doc.specs[0].diagram is not None
    assert doc.specs[0].diagram.path == "A.drawio.svg"


# --- GlossaryParser -----------------------------------------------------------

GLOSSARY_METADATA = Metadata(doc_type="glossary", title="A title", description="A description.")


def parse_glossary(body: str) -> tuple[GlossaryDoc, list[tuple[str, int | None]]]:
    """Parse ``body`` as if it started on line 6; return the structure and (code, line) of each finding."""
    doc, findings = GlossaryParser().parse(make_document({}, body=body), GLOSSARY_METADATA)
    assert doc is not None
    return doc, [(finding.code, finding.line) for finding in findings]


def test_terms_are_read_with_their_lines() -> None:
    doc, findings = parse_glossary(
        "<!-- guidance -->\n"  # 6
        "\n"  # 7
        "## Log file\n"  # 8
        "\n"  # 9
        "A file holding the samples of one session.\n"  # 10
        "\n"  # 11
        "## Sample\n"  # 12
        "One reading of one sensor channel.\n"  # 13
    )
    assert findings == []
    assert doc.metadata is GLOSSARY_METADATA
    assert doc.terms == (
        Term(term="Log file", definition="A file holding the samples of one session.", line=8, definition_line=10),
        Term(term="Sample", definition="One reading of one sensor channel.", line=12, definition_line=13),
    )


def test_a_definition_over_several_lines_is_kept_whole_for_the_validator() -> None:
    doc, findings = parse_glossary("## Sample\n\nOne reading\nof one channel.\n")
    assert findings == []
    assert doc.terms[0].definition == "One reading\nof one channel."


@pytest.mark.parametrize(
    ("body", "expected", "kept"),
    [
        ("Intro\n\n## Sample\n\nOne reading.\n", [("text-outside-term", 6)], 1),
        ("# Glossary\n\n## Sample\n\nOne reading.\n", [("heading-wrong-level", 6)], 1),
        ("## Sample\n\nOne reading. <!-- x -->\n", [("comment-not-whole-line", 8)], 1),
        ("##\n\nOne reading.\n", [("term-missing", 6)], 0),
        ("## Sample\n\n## Log file\n\nA file.\n", [("definition-missing", 6)], 1),
        ("## Sample\n\nOne reading.\n\nMore text.\nAnd more.\n", [("glossary-text-unexpected", 10)], 1),
        ("## Sample\n\nOne reading.\n- See also: Log file\n", [("glossary-text-unexpected", 9)], 1),
        ("## Sample\n\n- One reading.\n", [("glossary-text-unexpected", 8), ("definition-missing", 6)], 0),
    ],
)
def test_glossary_format_problems_are_parse_findings(body: str, expected: list[tuple[str, int]], kept: int) -> None:
    doc, findings = parse_glossary(body)
    assert findings == expected
    assert len(doc.terms) == kept


# --- OverviewParser -----------------------------------------------------------

OVERVIEW_METADATA = Metadata(doc_type="overview", title="A title", description="A description.")
SUMMARY_SECTION = "## Summary\n\nWhat it is.\n\n"  # lines 6-9
PURPOSE_SECTION = "## Purpose\n\nWhy it is built.\n\n"  # lines 10-13 when it follows the summary
DIAGRAM_SECTION = "## System diagram\n\n![System diagram](system_diagram.drawio.svg)\n"  # lines 14-16 when last


def parse_overview(body: str) -> tuple[OverviewDoc, list[tuple[str, int | None]]]:
    """Parse ``body`` as if it started on line 6; return the structure and (code, line) of each finding."""
    doc, findings = OverviewParser().parse(make_document({}, body=body), OVERVIEW_METADATA)
    assert doc is not None
    return doc, [(finding.code, finding.line) for finding in findings]


def test_the_three_sections_are_read_with_their_lines() -> None:
    doc, findings = parse_overview(SUMMARY_SECTION + PURPOSE_SECTION + DIAGRAM_SECTION)
    assert findings == []
    assert doc.metadata is OVERVIEW_METADATA
    assert doc.summary == TextSection(text="What it is.", line=8)
    assert doc.purpose == TextSection(text="Why it is built.", line=12)
    assert doc.system_diagram == Diagram(alt="System diagram", path="system_diagram.drawio.svg", line=16)


def test_a_paragraph_over_several_lines_is_kept_whole_for_the_validator() -> None:
    doc, findings = parse_overview("## Summary\n\nWhat\nit is.\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION)
    assert findings == []
    assert doc.summary is not None
    assert doc.summary.text == "What\nit is."


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (PURPOSE_SECTION + DIAGRAM_SECTION, [("overview-section-missing", None)]),
        (SUMMARY_SECTION + PURPOSE_SECTION, [("overview-section-missing", None)]),
        (
            SUMMARY_SECTION + "## Scope\n\nAnything.\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION,
            [("overview-section-unknown", 10)],
        ),
        (SUMMARY_SECTION + "## summary\n\nx\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION, [("overview-section-unknown", 10)]),
        (
            SUMMARY_SECTION + SUMMARY_SECTION + PURPOSE_SECTION + DIAGRAM_SECTION,
            [("overview-section-repeated", 10)],
        ),
        (PURPOSE_SECTION + SUMMARY_SECTION + DIAGRAM_SECTION, [("overview-section-out-of-order", 10)]),
        ("## Summary\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION, [("overview-section-empty", 6)]),
        (
            "## Summary\n\nWhat it is.\n\nMore.\n- a list\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION,
            [("overview-text-unexpected", 10)],
        ),
        ("## Summary\n\nWhat it is.\n- a list\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION, [("overview-text-unexpected", 9)]),
        (
            SUMMARY_SECTION + PURPOSE_SECTION + "## System diagram\n\nNo image here.\n",
            [
                ("overview-text-unexpected", 16),
                ("diagram-missing", 14),
            ],
        ),
        (
            SUMMARY_SECTION + PURPOSE_SECTION + '## System diagram\n\n<img src="system_diagram.drawio.svg">\n',
            [("overview-text-unexpected", 16), ("diagram-missing", 14)],
        ),
        (SUMMARY_SECTION + PURPOSE_SECTION + DIAGRAM_SECTION + "![Other](other.drawio.svg)\n", [("diagram-repeated", 17)]),
        ("Intro\n\n" + SUMMARY_SECTION + PURPOSE_SECTION + DIAGRAM_SECTION, [("text-outside-section", 6)]),
    ],
)
def test_overview_format_problems_are_parse_findings(body: str, expected: list[tuple[str, int | None]]) -> None:
    _, findings = parse_overview(body)
    assert findings == expected


def test_the_first_of_repeated_sections_and_images_is_used() -> None:
    body = "## Summary\n\nFirst.\n\n## Summary\n\nSecond.\n\n" + PURPOSE_SECTION + DIAGRAM_SECTION + "![b](b.drawio.svg)\n"
    doc, _ = parse_overview(body)
    assert doc.summary is not None
    assert doc.summary.text == "First."
    assert doc.system_diagram is not None
    assert doc.system_diagram.path == "system_diagram.drawio.svg"


@pytest.mark.parametrize("kind", ["requirement", "spec"])
@pytest.mark.parametrize(
    ("body", "line"),
    [
        # Right under the statement, the label would render as part of it.
        (f"{HEAD}The logger **shall** log.\nAcceptance criteria:\n\n- [ ] x\n", 13),
        # Right under a field, it would render inside the field's bullet.
        (f"{HEAD}The logger **shall** log.\n\n- Rationale: Why.\nAcceptance criteria:\n\n- [ ] x\n", 15),
    ],
)
def test_the_criteria_label_needs_a_blank_line_before_it(kind: str, body: str, line: int) -> None:
    count, findings = parse_entries(kind, body)
    assert (f"{kind}-criteria-not-separated", line) in findings
    assert count == 1


def test_a_spec_diagram_needs_a_blank_line_before_it() -> None:
    """Right under the last checkbox, the image would render inside it."""
    doc, findings = parse_specs(HEAD + BODY + "![Design](A.drawio.svg)\n")
    assert findings == [("spec-diagram-not-separated", 19)]
    assert doc.specs[0].diagram is not None
