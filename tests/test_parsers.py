from pathlib import Path

import pytest

from sks_tool.docs.base import Metadata
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.docs.glossary.term.block import Term
from sks_tool.docs.overview.doc import Diagram, OverviewDoc, TextSection
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document, load_document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.base import CommonParser
from sks_tool.parsers.glossary.parser import GlossaryParser
from sks_tool.parsers.overview.parser import OverviewParser
from sks_tool.parsers.requirements.parser import RequirementsParser

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


@pytest.mark.parametrize("name", ["specs"])
def test_type_parser_reads_any_body_while_blocks_are_undefined(name: str) -> None:
    document = make_document({"type": name, **FULL}, body="Anything\n")
    metadata = Metadata(doc_type=name, title="A title", description="A description.")
    structure, findings = DOC_TYPES[name].parser.parse(document, metadata)
    assert findings == []
    assert structure is not None
    assert structure.metadata is metadata


# --- RequirementsParser -------------------------------------------------------


def parse_requirements(body: str) -> tuple[RequirementsDoc, list[tuple[str, int | None]]]:
    """Parse ``body`` as if it started on line 6; return the structure and (code, line) of each finding."""
    doc, findings = RequirementsParser().parse(make_document({}, body=body), METADATA)
    assert doc is not None
    return doc, [(finding.code, finding.line) for finding in findings]


HEAD = "## A\n\nType: Functional\n\n"
"""A requirement's heading (line 6) and type line (line 8); its statement then starts on line 10."""


def test_requirements_are_read_with_their_lines() -> None:
    doc, findings = parse_requirements(
        "<!-- guidance\n"  # 6
        "     on two lines -->\n"  # 7
        "\n"  # 8
        "## LOG-001\n"  # 9
        "\n"  # 10
        "Type: Business\n"  # 11
        "\n"  # 12
        "The logger **shall** log.\n"  # 13
        "\n"  # 14
        "- Rationale: Because.\n"  # 15
        "\n"  # 16
        "## LOG-002 ##\n"  # 17
        "Type: Non-functional\n"  # 18: the type line may follow the heading directly
        "\n"  # 19
        "The logger **shall** beep.\n"  # 20
    )
    assert findings == []
    assert doc.metadata is METADATA
    assert doc.requirements == (
        Requirement(
            id="LOG-001",
            type="Business",
            statement="The logger **shall** log.",
            rationale="Because.",
            line=9,
            type_line=11,
            statement_line=13,
            rationale_line=15,
        ),
        Requirement(
            id="LOG-002",
            type="Non-functional",
            statement="The logger **shall** beep.",
            rationale=None,
            line=17,
            type_line=18,
            statement_line=20,
            rationale_line=None,
        ),
    )


@pytest.mark.parametrize(
    ("body", "expected_type"),
    [
        ("## A\n\nType: Functionnal\n\nThe logger **shall** log.\n", "Functionnal"),  # kept for the validator
        ("## A\n\nType:\n\nThe logger **shall** log.\n", ""),
    ],
)
def test_the_type_is_kept_as_written_for_the_validator(body: str, expected_type: str) -> None:
    doc, findings = parse_requirements(body)
    assert findings == []
    assert doc.requirements[0].type == expected_type


@pytest.mark.parametrize(
    "body",
    [
        "## A\n\nThe logger **shall** log.\n",  # no type line at all
        "## A\n\ntype: Functional\n\nThe logger **shall** log.\n",  # the label is exact: not a type line
        "## A\n\nThe logger **shall** log.\n\nType: Functional\n",  # the type line comes first
    ],
)
def test_a_requirement_without_a_type_line_first_is_reported_and_kept(body: str) -> None:
    doc, findings = parse_requirements(body)
    assert findings[0] == ("requirement-type-missing", 8)
    assert len(doc.requirements) == 1
    assert doc.requirements[0].type is None


def test_a_statement_right_after_the_type_line_is_reported_and_kept() -> None:
    """Without a blank line, Markdown would render the type and the statement as one paragraph."""
    doc, findings = parse_requirements("## A\n\nType: Functional\nThe logger **shall** log.\n")
    assert findings == [("requirement-type-not-separated", 9)]
    assert doc.requirements[0].type == "Functional"
    assert doc.requirements[0].statement == "The logger **shall** log."


def test_a_statement_over_several_lines_is_kept_whole_for_the_validator() -> None:
    doc, findings = parse_requirements(f"{HEAD}First line\nsecond line.\n")
    assert findings == []
    assert doc.requirements[0].statement == "First line\nsecond line."


def test_an_empty_rationale_is_kept_for_the_validator() -> None:
    doc, findings = parse_requirements(f"{HEAD}The logger **shall** log.\n\n- Rationale:\n")
    assert findings == []
    assert doc.requirements[0].rationale == ""


@pytest.mark.parametrize(
    ("body", "expected", "kept"),
    [
        # Outside requirements: only blank lines and comments.
        (f"Intro\nstill intro\n\n{HEAD}The logger **shall** log.\n", [("text-outside-requirement", 6)], 1),
        (f"# Title\n\n{HEAD}The logger **shall** log.\n", [("heading-wrong-level", 6)], 1),
        (f"{HEAD}The logger **shall** log.\n\n### Detail\n", [("heading-wrong-level", 12)], 1),
        (f"{HEAD}The logger **shall** log.\n<!-- never closed\n", [("comment-unterminated", 11)], 1),
        (f"{HEAD}The logger **shall** log. <!-- note -->\n", [("comment-not-whole-line", 10)], 1),
        (
            f"<!-- note --> trailing\n{HEAD}The logger **shall** log.\n",
            [("comment-not-whole-line", 6), ("text-outside-requirement", 6)],
            1,
        ),
        # Within a requirement.
        ("##\n\nType: Functional\n\nThe logger **shall** log.\n", [("requirement-id-missing", 6)], 0),
        (f"{HEAD}- Rationale: Why.\n", [("requirement-statement-missing", 6)], 0),
        (f"{HEAD}The logger **shall** log.\n\nMore text.\nAnd more.\n", [("requirement-text-unexpected", 12)], 1),
        (f"{HEAD}The logger **shall** log.\n\n- Notes: x\n", [("requirement-field-unknown", 12)], 1),
        (f"{HEAD}The logger **shall** log.\n\n- rationale: x\n", [("requirement-field-unknown", 12)], 1),
        (f"{HEAD}The logger **shall** log.\n\n- just a bullet\n", [("requirement-field-malformed", 12)], 1),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: x\n- Rationale: y\n",
            [("requirement-field-repeated", 13)],
            1,
        ),
        (
            f"{HEAD}The logger **shall** log.\n\n- Rationale: x\n  continued\n",
            [("requirement-field-continued", 13)],
            1,
        ),
    ],
)
def test_requirements_format_problems_are_parse_findings(body: str, expected: list[tuple[str, int]], kept: int) -> None:
    doc, findings = parse_requirements(body)
    assert findings == expected
    assert len(doc.requirements) == kept


def test_the_first_of_repeated_fields_is_used() -> None:
    doc, _ = parse_requirements(f"{HEAD}The logger **shall** log.\n\n- Rationale: x\n- Rationale: y\n")
    assert doc.requirements[0].rationale == "x"


def test_a_comment_after_an_id_is_reported_and_kept_out_of_the_id() -> None:
    """Otherwise '## A <!-- draft -->' would not clash with another '## A'."""
    doc, findings = parse_requirements("## A <!-- draft -->\n\nType: Functional\n\nThe logger **shall** log. <!-- x -->\n")
    assert findings == [("comment-not-whole-line", 6), ("comment-not-whole-line", 10)]
    assert doc.requirements[0].id == "A"
    assert doc.requirements[0].statement == "The logger **shall** log."


def test_a_comment_inside_a_rationale_does_not_count_toward_its_length() -> None:
    doc, findings = parse_requirements(f"{HEAD}The logger **shall** log.\n\n- Rationale: Why. <!-- x -->\n")
    assert findings == [("comment-not-whole-line", 12)]
    assert doc.requirements[0].rationale == "Why."


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
