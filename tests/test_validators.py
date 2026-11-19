from pathlib import Path

import pytest

from sks_tool.docs.base import Metadata
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.document import Document
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.base import CommonValidator
from sks_tool.validators.project import ProjectValidator
from sks_tool.validators.requirements.requirement.validator import RequirementValidator
from sks_tool.validators.requirements.validator import RequirementsValidator

METADATA = Metadata(doc_type="requirements", title="A title", description="A description.")
DOCUMENT = Document(path=Path("doc.md"), front_matter={}, body="", body_line=6)


def requirement(statement: str, rationale: str | None = None, id: str = "LOG-001", line: int = 10) -> Requirement:
    return Requirement(
        id=id,
        statement=statement,
        rationale=rationale,
        line=line,
        statement_line=line + 2,
        rationale_line=None if rationale is None else line + 4,
    )


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
        ("requirement-id-duplicate", 6),
        ("requirement-id-duplicate", 10),
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
