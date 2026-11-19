from pathlib import Path

import pytest

from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document, load_document
from sks_tool.findings import ParserFinding
from sks_tool.parsers.base import CommonParser


def make_document(front_matter: dict[str, object]) -> Document:
    return Document(path=Path("doc.md"), front_matter=front_matter, body="", body_line=4)


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


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_common_parser_resolves_each_type(name: str) -> None:
    doc_type, findings = CommonParser(DOC_TYPES).parse(make_document({"type": name}))
    assert findings == []
    assert doc_type is DOC_TYPES[name]


@pytest.mark.parametrize(
    ("front_matter", "code"),
    [
        ({}, "type-missing"),
        ({"type": 3}, "type-not-text"),
        ({"type": "recipe"}, "type-unknown"),
    ],
)
def test_common_parser_reports_an_unusable_type(front_matter: dict[str, object], code: str) -> None:
    doc_type, findings = CommonParser(DOC_TYPES).parse(make_document(front_matter))
    assert doc_type is None
    assert [finding.code for finding in findings] == [code]


def test_common_parser_hint_lists_the_known_types() -> None:
    _, findings = CommonParser(DOC_TYPES).parse(make_document({"type": "recipe"}))
    assert all(name in findings[0].hint for name in DOC_TYPES)


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_type_parser_reads_any_body_while_blocks_are_undefined(name: str) -> None:
    document = make_document({"type": name})
    structure, findings = DOC_TYPES[name].parser.parse(document)
    assert findings == []
    assert structure is not None
    assert structure.document is document
