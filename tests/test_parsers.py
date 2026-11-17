from importlib import resources
from pathlib import Path

import pytest

from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import load_document
from sks_tool.parsers.common import validate_file


def write(tmp_path: Path, text: str, name: str = "doc.md") -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def codes(path: Path) -> list[str]:
    return [issue.code for issue in validate_file(path).issues]


def test_expected_document_types() -> None:
    assert list(DOC_TYPES) == ["requirements", "specs", "overview", "glossary"]


def test_every_template_file_belongs_to_a_type() -> None:
    templates = resources.files("sks_tool").joinpath("templates")
    assert sorted(entry.name for entry in templates.iterdir()) == sorted(f"{name}.md" for name in DOC_TYPES)


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_template_passes_its_own_parser(tmp_path: Path, name: str) -> None:
    """The templates are the known-good reference: each must validate cleanly."""
    path = write(tmp_path, DOC_TYPES[name].template())
    result = validate_file(path)
    assert result.issues == []
    assert result.doc_type == name


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_template_is_the_type_header_and_its_summary(name: str) -> None:
    """A template holds nothing but its type and its summary as a guidance comment."""
    doc_type = DOC_TYPES[name]
    header, _, body = doc_type.template().partition("\n---\n")
    assert header == f"---\ntype: {name}"
    assert " ".join(body.split()) == f"<!-- {doc_type.summary} -->"


def test_document_is_split_into_front_matter_and_body(tmp_path: Path) -> None:
    path = write(tmp_path, "---\ntype: glossary\nextra: 1\n---\n\n# Heading\n")
    document, issues = load_document(path)
    assert issues == []
    assert document is not None
    assert document.front_matter == {"type": "glossary", "extra": 1}
    assert document.body == "\n# Heading\n"
    assert document.body_line == 5


@pytest.mark.parametrize(
    "text",
    [
        "---\r\ntype: glossary\r\n---\r\n\r\nBody\r\n",  # Windows line endings
        "﻿---\ntype: glossary\n---\n",  # byte-order mark
        "---\ntype: glossary\n---",  # no trailing newline
    ],
)
def test_encoding_and_line_ending_variants_are_accepted(tmp_path: Path, text: str) -> None:
    assert codes(write(tmp_path, text)) == []


@pytest.mark.parametrize(
    ("text", "code", "line"),
    [
        ("", "front-matter-missing", 1),
        ("# Just Markdown\n", "front-matter-missing", 1),
        ("\n---\ntype: glossary\n---\n", "front-matter-missing", 1),
        ("---\ntype: glossary\n", "front-matter-unterminated", 1),
        ("---\ntype: glossary\nbad: [unclosed\n---\n", "front-matter-invalid-yaml", 3),
        ("---\n- a\n- b\n---\n", "front-matter-not-mapping", 2),
        ("---\n---\n", "type-missing", None),
        ("---\ntitle: No type\n---\n", "type-missing", None),
        ("---\ntype: 3\n---\n", "type-not-text", None),
        ("---\ntype: recipe\n---\n", "type-unknown", None),
        ("---\ntype: Glossary\n---\n", "type-unknown", None),
    ],
)
def test_invalid_documents_are_reported(tmp_path: Path, text: str, code: str, line: int | None) -> None:
    result = validate_file(write(tmp_path, text))
    assert [(issue.code, issue.line) for issue in result.issues] == [(code, line)]
    assert result.doc_type is None


def test_missing_file_is_reported(tmp_path: Path) -> None:
    assert codes(tmp_path / "absent.md") == ["file-not-found"]


def test_non_utf8_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_bytes(b"---\ntype: glossary\n---\n\xff\xfe\n")
    assert codes(path) == ["file-not-utf8"]
