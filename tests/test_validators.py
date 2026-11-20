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
from sks_tool.doctypes import BLANK_DIAGRAM as BLANK_DIAGRAM_TEMPLATE
from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.base import CommonValidator
from sks_tool.validators.glossary.term.validator import TermValidator
from sks_tool.validators.glossary.validator import GlossaryValidator
from sks_tool.validators.overview.validator import OverviewValidator
from sks_tool.validators.project import ProjectValidator
from sks_tool.validators.requirements.requirement.validator import RequirementValidator
from sks_tool.validators.requirements.validator import RequirementsValidator
from sks_tool.validators.specs.spec.validator import SpecValidator
from sks_tool.validators.specs.validator import SpecsValidator

METADATA = Metadata(doc_type="requirements", title="A title", description="A description.")
DOCUMENT = Document(path=Path("doc.md"), front_matter={}, body="", body_line=6)


PENDING_CRITERIA = (AcceptanceCriterion(text="It works.", checked=False, line=30),)


def requirement(
    statement: str,
    rationale: str | None = None,
    id: str = "LOG-001",
    line: int = 10,
    type: str | None = "Functional",
    status: str | None = "Pending",
    criteria: tuple[AcceptanceCriterion, ...] = PENDING_CRITERIA,
) -> Requirement:
    return Requirement(
        id=id,
        type=type,
        status=status,
        statement=statement,
        rationale=rationale,
        criteria=criteria,
        line=line,
        type_line=None if type is None else line + 1,
        status_line=None if status is None else line + 3,
        statement_line=line + 2,
        rationale_line=None if rationale is None else line + 4,
    )


def criteria(*marks: bool) -> tuple[AcceptanceCriterion, ...]:
    """Criteria checked or not, in order, on lines 30 onwards."""
    return tuple(AcceptanceCriterion(text=f"Criterion {i}.", checked=mark, line=30 + i) for i, mark in enumerate(marks))


def codes(findings: list[ValidatorFinding]) -> list[str]:
    return [finding.code for finding in findings]


# --- CommonValidator ----------------------------------------------------------


def test_common_validator_accepts_valid_metadata() -> None:
    assert CommonValidator().validate(METADATA) == []


def test_common_validator_skips_keys_the_parser_already_reported() -> None:
    assert CommonValidator().validate(Metadata(doc_type=None, title=None, description=None)) == []


@pytest.mark.parametrize(
    ("title", "description", "expected"),
    [
        ("One two three four five", " ".join(["word"] * 100), []),
        ("One two three four five six", "Fine.", ["title-too-long"]),
        ("  ", "Fine.", ["title-empty"]),
        ("Fine", " ".join(["word"] * 101), ["description-too-long"]),
        ("Fine", "", ["description-empty"]),
    ],
)
def test_common_validator_limits_title_and_description_words(title: str, description: str, expected: list[str]) -> None:
    findings = CommonValidator().validate(Metadata(doc_type="glossary", title=title, description=description))
    assert codes(findings) == expected
    assert all(finding.location[0] == "front matter" for finding in findings)


# --- RequirementValidator -----------------------------------------------------


@pytest.mark.parametrize(
    "statement",
    [
        "The logger **shall** sample each accelerometer axis at 1 kHz.",
        "The supply **shall** stay within 3.3 V and 5.0 V.",  # a '.' inside a number is not a sentence end
        "The logger **shall** " + "x" * 82 + ".",  # 100 characters as rendered, 104 as written
    ],
)
def test_valid_statements_pass(statement: str) -> None:
    assert RequirementValidator().validate(requirement(statement)) == []


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("The logger **shall** log\nall samples.", ["statement-not-one-line"]),
        ("The logger **shall** log", ["statement-no-final-period"]),
        ("The logger **shall** log!", ["statement-no-final-period"]),
        ("The logger **shall** log. Then it rests.", ["statement-several-sentences"]),
        ("The logger **shall** log sensors, e.g. the IMU.", ["statement-several-sentences"]),
        ("The logger logs.", ["statement-shall-missing"]),
        ("The logger **shall** log and **shall** beep.", ["statement-shall-repeated"]),
        ("The logger shall log.", ["statement-shall-not-bold"]),
        ("The logger **Shall** log.", ["statement-shall-not-bold"]),
        ("The logger **shall** " + "x" * 83 + ".", ["statement-too-long"]),
        ("The marshall **shall** log.", []),  # "shall" inside another word does not count
        ("The logger **shall** not overwrite a log file.", ["statement-negative"]),
        ("The logger **shall not** overwrite a log file.", ["statement-negative"]),
        ("The logger shall not overwrite a log file.", ["statement-shall-not-bold", "statement-negative"]),
        ("The logger **shall** notify the pilot.", []),  # "not" inside another word does not count
    ],
)
def test_statement_rules(statement: str, expected: list[str]) -> None:
    findings = RequirementValidator().validate(requirement(statement))
    assert codes(findings) == expected
    assert all(finding.location == ("requirement LOG-001", "statement") for finding in findings)
    assert all(finding.line == 12 for finding in findings)


@pytest.mark.parametrize(
    ("rationale", "expected"),
    [
        (None, []),
        ("x" * 200, []),
        ("x" * 201, ["rationale-too-long"]),
        ("", ["rationale-empty"]),
        ("   ", ["rationale-empty"]),
    ],
)
def test_rationale_rules(rationale: str | None, expected: list[str]) -> None:
    findings = RequirementValidator().validate(requirement("The logger **shall** log.", rationale))
    assert codes(findings) == expected
    assert all(finding.location == ("requirement LOG-001", "rationale") for finding in findings)
    assert all(finding.line == 14 for finding in findings)


@pytest.mark.parametrize("valid", ["Business", "Functional", "Non-functional"])
def test_each_requirement_type_passes(valid: str) -> None:
    assert RequirementValidator().validate(requirement("The logger **shall** log.", type=valid)) == []


def test_a_missing_type_is_not_reported_again() -> None:
    """The parser already reported the missing type line."""
    assert RequirementValidator().validate(requirement("The logger **shall** log.", type=None)) == []


@pytest.mark.parametrize(
    ("written", "message"),
    [
        ("Functionnal", "'Functionnal' is not a requirement type"),
        ("functional", "'functional' is not a requirement type"),  # matched exactly
        ("Non functional", "'Non functional' is not a requirement type"),
        ("", "is empty"),
    ],
)
def test_an_unknown_type_is_a_validation_finding(written: str, message: str) -> None:
    findings = RequirementValidator().validate(requirement("The logger **shall** log.", type=written))
    assert [(finding.code, finding.message) for finding in findings] == [("requirement-type-unknown", message)]
    assert findings[0].location == ("requirement LOG-001", "type")
    assert findings[0].line == 11
    assert "Business, Functional, Non-functional" in findings[0].hint


# --- RequirementsValidator ----------------------------------------------------


def test_a_requirements_document_needs_at_least_one_requirement() -> None:
    doc = RequirementsDoc(metadata=METADATA, document=DOCUMENT, requirements=())
    assert codes(RequirementsValidator().validate(doc)) == ["requirements-none"]


def test_each_requirement_of_the_document_is_validated() -> None:
    doc = RequirementsDoc(
        metadata=METADATA,
        document=DOCUMENT,
        requirements=(requirement("The logger logs.", id="A"), requirement("The logger **shall** log.", id="B")),
    )
    findings = RequirementsValidator().validate(doc)
    assert [(finding.code, finding.location[0]) for finding in findings] == [("statement-shall-missing", "requirement A")]


# --- ProjectValidator ---------------------------------------------------------


def requirements_doc(*ids_and_lines: tuple[str, int]) -> RequirementsDoc:
    return RequirementsDoc(
        metadata=METADATA,
        document=DOCUMENT,
        requirements=tuple(requirement("The logger **shall** log.", id=id, line=line) for id, line in ids_and_lines),
    )


def test_unique_ids_pass() -> None:
    structures = {"a.md": requirements_doc(("A", 6), ("B", 10)), "b.md": requirements_doc(("C", 6))}
    assert ProjectValidator().validate(structures) == {}


def test_an_id_used_twice_in_one_document_is_reported_at_both_places() -> None:
    findings = ProjectValidator().validate({"a.md": requirements_doc(("A", 6), ("A", 10))})
    assert [(finding.code, finding.line) for finding in findings["a.md"]] == [
        ("id-duplicate", 6),
        ("id-duplicate", 10),
    ]
    assert "also used at a.md:10" in findings["a.md"][0].hint
    assert "also used at a.md:6" in findings["a.md"][1].hint


def test_an_id_used_across_documents_is_reported_in_each() -> None:
    structures = {"a.md": requirements_doc(("A", 6)), "b.md": requirements_doc(("B", 6), ("A", 10)), "c": object()}
    findings = ProjectValidator().validate(structures)
    assert set(findings) == {"a.md", "b.md"}
    assert findings["a.md"][0].hint.endswith("'A' is also used at b.md:10")
    assert findings["b.md"][0].hint.endswith("'A' is also used at a.md:6")
    assert findings["b.md"][0].location == ("requirement A",)


# --- TermValidator and GlossaryValidator --------------------------------------


def term(name: str, definition: str = "What it means.", line: int = 10) -> Term:
    return Term(term=name, definition=definition, line=line, definition_line=line + 2)


def glossary(*terms: Term) -> GlossaryDoc:
    return GlossaryDoc(metadata=METADATA, document=DOCUMENT, terms=terms)


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (term("x" * 100, "y" * 200), []),
        (term("x" * 101), ["term-too-long"]),
        (term("Sample", "y" * 201), ["definition-too-long"]),
        (term("Sample", "One reading\nof one channel."), ["definition-not-one-line"]),
    ],
)
def test_term_rules(entry: Term, expected: list[str]) -> None:
    assert codes(TermValidator().validate(entry)) == expected


def test_term_findings_name_the_term_and_point_at_its_lines() -> None:
    term_finding, definition_finding = TermValidator().validate(term("x" * 101, "y" * 201))
    assert (term_finding.location, term_finding.line) == (("term '" + "x" * 101 + "'",), 10)
    assert (definition_finding.location, definition_finding.line) == (("term '" + "x" * 101 + "'", "definition"), 12)


def test_a_glossary_needs_at_least_one_term() -> None:
    assert codes(GlossaryValidator().validate(glossary())) == ["glossary-none"]


def test_terms_in_alphabetical_order_ignoring_case_pass() -> None:
    doc = glossary(term("hold-up capacitor"), term("Log file"), term("Logger"), term("sample"))
    assert GlossaryValidator().validate(doc) == []


def test_a_misplaced_term_gives_a_single_finding() -> None:
    doc = glossary(term("Alpha", line=6), term("Zulu", line=8), term("Bravo", line=10), term("Charlie", line=12))
    findings = GlossaryValidator().validate(doc)
    assert [(finding.code, finding.line) for finding in findings] == [("term-out-of-order", 10)]
    assert findings[0].message == "comes after 'Zulu'"
    assert findings[0].hint == "sort the terms alphabetically; 'Bravo' belongs before 'Zulu'"


def test_each_term_of_the_glossary_is_validated() -> None:
    findings = GlossaryValidator().validate(glossary(term("A"), term("B", "y" * 201)))
    assert [(finding.code, finding.location[0]) for finding in findings] == [("definition-too-long", "term 'B'")]


def test_a_term_defined_in_two_glossaries_is_reported_in_each_ignoring_case() -> None:
    structures = {"a.md": glossary(term("Log file", line=6)), "b.md": glossary(term("log FILE", line=9))}
    findings = ProjectValidator().validate(structures)
    assert [(finding.code, finding.line) for finding in findings["a.md"]] == [("term-duplicate", 6)]
    assert findings["a.md"][0].hint == "define each term once; 'Log file' is also defined at b.md:9"
    assert findings["b.md"][0].hint == "define each term once; 'log FILE' is also defined at a.md:6"
    assert findings["b.md"][0].location == ("term 'log FILE'",)


def test_terms_and_requirement_ids_do_not_clash() -> None:
    structures = {"g.md": glossary(term("LOG-001")), "r.md": requirements_doc(("LOG-001", 6))}
    assert ProjectValidator().validate(structures) == {}


# --- OverviewValidator --------------------------------------------------------

BLANK_DIAGRAM = DOC_TYPES["overview"].companion(BLANK_DIAGRAM_TEMPLATE)


def overview(
    folder: Path,
    summary: str | None = "What it is.",
    purpose: str | None = "Why it is built.",
    diagram_path: str | None = "system_diagram.drawio.svg",
) -> OverviewDoc:
    return OverviewDoc(
        metadata=METADATA,
        document=Document(path=folder / "overview.md", front_matter={}, body="", body_line=6),
        summary=None if summary is None else TextSection(text=summary, line=8),
        purpose=None if purpose is None else TextSection(text=purpose, line=12),
        system_diagram=None if diagram_path is None else Diagram(alt="System diagram", path=diagram_path, line=16),
    )


def test_a_complete_overview_passes(tmp_path: Path) -> None:
    (tmp_path / "system_diagram.drawio.svg").write_bytes(BLANK_DIAGRAM)
    assert OverviewValidator().validate(overview(tmp_path)) == []


def test_missing_sections_are_not_reported_again(tmp_path: Path) -> None:
    """The parser already reported them."""
    assert OverviewValidator().validate(overview(tmp_path, summary=None, purpose=None, diagram_path=None)) == []


@pytest.mark.parametrize(
    ("summary", "purpose", "expected"),
    [
        ("x" * 200, "y" * 200, []),
        ("x" * 201, "Why.", ["summary-too-long"]),
        ("What.", "y" * 201, ["purpose-too-long"]),
        ("What\nit is.", "Why.", ["summary-not-one-line"]),
        ("What.", "Why\nit is built.", ["purpose-not-one-line"]),
    ],
)
def test_summary_and_purpose_rules(tmp_path: Path, summary: str, purpose: str, expected: list[str]) -> None:
    (tmp_path / "system_diagram.drawio.svg").write_bytes(BLANK_DIAGRAM)
    findings = OverviewValidator().validate(overview(tmp_path, summary=summary, purpose=purpose))
    assert codes(findings) == expected


@pytest.mark.parametrize(
    ("path", "content", "expected"),
    [
        ("diagrams/system_diagram.drawio.svg", BLANK_DIAGRAM, []),  # resolved from the document's folder
        ("https://example.com/d.drawio.svg", None, ["diagram-path-not-relative"]),
        ("/abs/system_diagram.drawio.svg", None, ["diagram-path-not-relative"]),
        ("C:/abs/system_diagram.drawio.svg", None, ["diagram-path-not-relative"]),
        ("system_diagram.svg", None, ["diagram-not-drawio-svg"]),
        ("system_diagram.drawio", None, ["diagram-not-drawio-svg"]),
        ("absent.drawio.svg", None, ["diagram-file-not-found"]),
        ("plain.drawio.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>', ["diagram-not-editable"]),
        ("binary.drawio.svg", b"\xff\xfe\x00", ["diagram-not-editable"]),
    ],
)
def test_diagram_rules(tmp_path: Path, path: str, content: bytes | None, expected: list[str]) -> None:
    if content is not None:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    findings = OverviewValidator().validate(overview(tmp_path, diagram_path=path))
    assert codes(findings) == expected
    assert all((finding.location, finding.line) == (("system diagram",), 16) for finding in findings)


def test_a_spec_cannot_reuse_a_requirement_id() -> None:
    structures = {"r.md": requirements_doc(("LOG-001", 6)), "s.md": specs_doc(spec(id="LOG-001", line=8))}
    findings = ProjectValidator().validate(structures)
    assert [(finding.code, finding.location) for finding in findings["s.md"]] == [("id-duplicate", ("spec LOG-001",))]
    assert findings["s.md"][0].hint.endswith("'LOG-001' is also used at r.md:6")
    assert findings["r.md"][0].hint.endswith("'LOG-001' is also used at s.md:8")


# --- Status and acceptance criteria (requirements and specs) ------------------


@pytest.mark.parametrize(
    ("status", "marks", "expected"),
    [
        ("Pending", (False, False), []),
        ("Pending", (True, False), ["status-pending-checked"]),
        ("Pending", (True, True), ["status-pending-checked"]),  # one finding, not two
        ("Underway", (True, False), []),
        ("Underway", (False, False), []),
        ("Underway", (True, True), ["status-all-checked"]),
        ("Unfulfilled", (True, False), []),
        ("Unfulfilled", (True, True), ["status-all-checked"]),
        ("Fulfilled", (True, True), []),
        ("Fulfilled", (True, False), ["status-fulfilled-unchecked"]),
    ],
)
def test_the_checkboxes_agree_with_the_status(status: str, marks: tuple[bool, ...], expected: list[str]) -> None:
    findings = RequirementValidator().validate(
        requirement("The logger **shall** log.", status=status, criteria=criteria(*marks))
    )
    assert codes(findings) == expected
    assert all((finding.location, finding.line) == (("requirement LOG-001", "status"), 13) for finding in findings)


@pytest.mark.parametrize(
    ("written", "message"),
    [("Done", "'Done' is not a requirement status"), ("pending", "'pending' is not a requirement status"), ("", "is empty")],
)
def test_an_unknown_status_is_reported_and_not_compared_with_the_checkboxes(written: str, message: str) -> None:
    findings = RequirementValidator().validate(
        requirement("The logger **shall** log.", status=written, criteria=criteria(True, True))
    )
    assert [(finding.code, finding.message) for finding in findings] == [("requirement-status-unknown", message)]
    assert "Pending, Unfulfilled, Underway, Fulfilled" in findings[0].hint


def test_a_missing_status_is_not_reported_again() -> None:
    """The parser already reported the missing status line."""
    assert RequirementValidator().validate(requirement("The logger **shall** log.", status=None)) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [("x" * 200, []), ("x" * 201, ["criterion-too-long"]), ("", ["criterion-empty"])],
)
def test_criterion_rules(text: str, expected: list[str]) -> None:
    entry = requirement("The logger **shall** log.", criteria=(AcceptanceCriterion(text=text, checked=False, line=31),))
    findings = RequirementValidator().validate(entry)
    assert codes(findings) == expected
    assert all(
        (finding.location, finding.line) == (("requirement LOG-001", "acceptance criteria"), 31) for finding in findings
    )


# --- SpecValidator and SpecsValidator -----------------------------------------


def spec(
    statement: str = "The logger batches its flash writes.",
    rationale: str | None = "Flash writes are slow.",
    id: str = "LOG-S-001",
    line: int = 10,
    type: str | None = "Non-functional",
    diagram: str | None = None,
) -> Spec:
    return Spec(
        id=id,
        type=type,
        status="Pending",
        statement=statement,
        rationale=rationale,
        criteria=PENDING_CRITERIA,
        diagram=None if diagram is None else Diagram(alt="Design", path=diagram, line=40),
        line=line,
        type_line=None if type is None else line + 1,
        status_line=line + 3,
        statement_line=line + 2,
        rationale_line=None if rationale is None else line + 4,
    )


def specs_doc(*specs: Spec) -> SpecsDoc:
    return SpecsDoc(metadata=METADATA, document=DOCUMENT, specs=specs)


def test_a_valid_spec_passes(tmp_path: Path) -> None:
    assert SpecValidator(tmp_path).validate(spec()) == []


@pytest.mark.parametrize("valid", ["Functional", "Non-functional"])
def test_each_spec_type_passes(tmp_path: Path, valid: str) -> None:
    assert SpecValidator(tmp_path).validate(spec(type=valid)) == []


def test_a_spec_has_no_business_type(tmp_path: Path) -> None:
    findings = SpecValidator(tmp_path).validate(spec(type="Business"))
    assert [(finding.code, finding.message) for finding in findings] == [
        ("spec-type-unknown", "'Business' is not a spec type")
    ]
    assert findings[0].hint.endswith("a business requirement belongs in a requirements document")


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("x" * 199 + ".", []),  # 200 characters
        ("x" * 200 + ".", ["statement-too-long"]),
        ("The logger batches writes. Then it flushes.", ["statement-several-sentences"]),
        ("The logger batches writes", ["statement-no-final-period"]),
        ("The logger batches\nits writes.", ["statement-not-one-line"]),
        ("The logger **shall** batch its writes.", []),  # no rule about "shall" in a spec
    ],
)
def test_spec_statement_rules(tmp_path: Path, statement: str, expected: list[str]) -> None:
    findings = SpecValidator(tmp_path).validate(spec(statement=statement))
    assert codes(findings) == expected
    assert all(finding.location == ("spec LOG-S-001", "statement") for finding in findings)


def test_a_missing_spec_rationale_is_not_reported_again(tmp_path: Path) -> None:
    """The parser already reported it."""
    assert SpecValidator(tmp_path).validate(spec(rationale=None)) == []


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("LOG-S-001.drawio.svg", []),
        ("diagrams/LOG-S-001.drawio.svg", []),  # any folder, relative to the document
        ("ring_buffer.drawio.svg", ["diagram-name-mismatch"]),
        ("LOG-S-001.svg", ["diagram-not-drawio-svg"]),
    ],
)
def test_a_spec_diagram_is_named_after_its_id(tmp_path: Path, path: str, expected: list[str]) -> None:
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(BLANK_DIAGRAM)
    findings = SpecValidator(tmp_path).validate(spec(diagram=path))
    assert codes(findings) == expected
    assert all((finding.location, finding.line) == (("spec LOG-S-001", "diagram"), 40) for finding in findings)


def test_a_specs_document_needs_at_least_one_spec() -> None:
    assert codes(SpecsValidator().validate(specs_doc())) == ["specs-none"]


def test_each_spec_of_the_document_is_validated_with_its_folder(tmp_path: Path) -> None:
    doc = SpecsDoc(
        metadata=METADATA,
        document=Document(path=tmp_path / "specs.md", front_matter={}, body="", body_line=6),
        specs=(spec(id="A"), spec(id="B", diagram="B.drawio.svg")),
    )
    findings = SpecsValidator().validate(doc)
    assert [(finding.code, finding.location[0]) for finding in findings] == [("diagram-file-not-found", "spec B")]


@pytest.mark.parametrize(
    ("status", "marks", "message"),
    [
        ("Fulfilled", (True, False), "is Fulfilled but 1 criterion is unchecked"),
        ("Fulfilled", (False, False), "is Fulfilled but 2 criteria are unchecked"),
        ("Pending", (True, False), "is Pending but 1 criterion is checked"),
    ],
)
def test_status_mismatch_messages_count_the_criteria(status: str, marks: tuple[bool, ...], message: str) -> None:
    entry = requirement("The logger **shall** log.", status=status, criteria=criteria(*marks))
    assert [finding.message for finding in RequirementValidator().validate(entry)] == [message]


@pytest.mark.parametrize(
    ("entry_id", "message"),
    [
        ("LOG-001", None),
        ("LOG 001", "the ID contains whitespace"),
        ("LOG-001(a)", "the ID contains parentheses"),
        ("LOG (1)", "the ID contains whitespace and parentheses"),
    ],
)
def test_an_id_has_no_whitespace_or_parentheses(tmp_path: Path, entry_id: str, message: str | None) -> None:
    for findings, entry in (
        (RequirementValidator().validate(requirement("The logger **shall** log.", id=entry_id)), "requirement"),
        (SpecValidator(tmp_path).validate(spec(id=entry_id)), "spec"),
    ):
        expected = [] if message is None else [("id-invalid", message, (f"{entry} {entry_id}",), 10)]
        assert [(finding.code, finding.message, finding.location, finding.line) for finding in findings] == expected
