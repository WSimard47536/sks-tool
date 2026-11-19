from dataclasses import replace
from importlib import resources
from pathlib import Path

import pytest

from sks_tool import pipeline
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document
from sks_tool.findings import ParserFinding, ValidatorFinding
from sks_tool.parsers.base import Parser
from sks_tool.pipeline import check_file
from sks_tool.validators.base import Validator


def write(tmp_path: Path, text: str, name: str = "doc.md") -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def codes(path: Path) -> list[str]:
    return [finding.code for finding in check_file(path).findings]


def test_expected_document_types() -> None:
    assert list(DOC_TYPES) == ["requirements", "specs", "overview", "glossary"]


def test_every_template_file_belongs_to_a_type() -> None:
    templates = resources.files("sks_tool").joinpath("templates")
    assert sorted(entry.name for entry in templates.iterdir()) == sorted(f"{name}.md" for name in DOC_TYPES)


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_template_passes_its_own_parser_and_validator(tmp_path: Path, name: str) -> None:
    """The templates are the known-good reference: each must be read and validated cleanly."""
    result = check_file(write(tmp_path, DOC_TYPES[name].template()))
    assert result.findings == []
    assert result.validated
    assert result.ok
    assert result.doc_type == name


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_template_is_the_type_header_and_its_summary(name: str) -> None:
    """A template holds nothing but its type and its summary as a guidance comment."""
    doc_type = DOC_TYPES[name]
    header, _, body = doc_type.template().partition("\n---\n")
    assert header == f"---\ntype: {name}"
    assert " ".join(body.split()) == f"<!-- {doc_type.summary} -->"


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
def test_unreadable_documents_are_parse_findings_and_skip_validation(
    tmp_path: Path, text: str, code: str, line: int | None
) -> None:
    result = check_file(write(tmp_path, text))
    parse_findings = [finding for finding in result.findings if isinstance(finding, ParserFinding)]
    assert parse_findings == result.findings
    assert [(finding.code, finding.line) for finding in parse_findings] == [(code, line)]
    assert result.doc_type is None
    assert not result.validated
    assert not result.ok


def test_missing_file_is_reported(tmp_path: Path) -> None:
    assert codes(tmp_path / "absent.md") == ["file-not-found"]


def test_non_utf8_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_bytes(b"---\ntype: glossary\n---\n\xff\xfe\n")
    assert codes(path) == ["file-not-utf8"]


class _ParserWithFinding:
    def parse(self, document: Document) -> tuple[None, list[ParserFinding]]:
        return None, [ParserFinding(code="block-broken", message="a block is broken", hint="fix the block")]


class _ParserWithoutFinding:
    def parse(self, document: Document) -> tuple[None, list[ParserFinding]]:
        return None, []


class _ParserRecoveringWithFinding:
    """Reads the document but reports a problem it could work around."""

    def parse(self, document: Document) -> tuple[GlossaryDoc | None, list[ParserFinding]]:
        finding = ParserFinding(code="block-odd", message="a block is odd", hint="tidy the block", line=4)
        return GlossaryDoc(document=document), [finding]


class _RecordingValidator:
    def __init__(self) -> None:
        self.seen: list[GlossaryDoc] = []

    def validate(self, doc: GlossaryDoc) -> list[ValidatorFinding]:
        self.seen.append(doc)
        return [ValidatorFinding(code="rule-broken", message="a rule is broken", hint="follow the rule")]


def _use_parser(
    monkeypatch: pytest.MonkeyPatch, parser: Parser[GlossaryDoc | None], validator: Validator[GlossaryDoc] | None = None
) -> None:
    patched = {
        name: replace(doc_type, parser=parser, validator=validator or doc_type.validator)
        for name, doc_type in DOC_TYPES.items()
    }
    monkeypatch.setattr(pipeline, "DOC_TYPES", patched)


def test_a_parser_that_recovers_still_has_the_document_validated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    validator = _RecordingValidator()
    _use_parser(monkeypatch, _ParserRecoveringWithFinding(), validator)
    result = check_file(write(tmp_path, "---\ntype: glossary\n---\n"))
    assert [(finding.kind, finding.code) for finding in result.findings] == [
        ("parse", "block-odd"),
        ("validate", "rule-broken"),
    ]
    assert len(validator.seen) == 1
    assert result.validated
    assert not result.ok


def test_a_failed_type_parser_skips_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_parser(monkeypatch, _ParserWithFinding())
    result = check_file(write(tmp_path, "---\ntype: glossary\n---\n"))
    assert [finding.code for finding in result.findings] == ["block-broken"]
    assert result.doc_type == "glossary"
    assert not result.validated
    assert not result.ok


def test_a_parser_failing_without_a_finding_stops_the_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A parser that gives up silently is a bug: it must never let a document pass unchecked."""
    _use_parser(monkeypatch, _ParserWithoutFinding())
    with pytest.raises(RuntimeError, match="internal error"):
        check_file(write(tmp_path, "---\ntype: glossary\n---\n"))


def test_shared_checks_run_even_when_the_type_is_unusable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectingCommonValidator:
        def validate(self, document: Document) -> list[ValidatorFinding]:
            return [ValidatorFinding(code="shared-rule", message="a shared rule is broken", hint="follow it")]

    monkeypatch.setattr(pipeline, "CommonValidator", RejectingCommonValidator)
    result = check_file(write(tmp_path, "---\ntype: recipe\n---\n"))
    assert [(finding.kind, finding.code) for finding in result.findings] == [
        ("parse", "type-unknown"),
        ("validate", "shared-rule"),
    ]
    assert not result.validated
