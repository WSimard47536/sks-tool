from dataclasses import replace
from importlib import resources
from pathlib import Path

import pytest
import yaml

from sks_tool import pipeline
from sks_tool.docs.base import Metadata
from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document
from sks_tool.findings import ParserFinding, ValidatorFinding
from sks_tool.parsers.base import Parser
from sks_tool.pipeline import check_file, check_project
from sks_tool.validators.base import Validator

META = "title: A title\ndescription: A description.\n"
"""Front matter lines for the keys every document needs besides ``type``."""


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
def test_template_starts_with_its_metadata_and_its_summary(name: str) -> None:
    """A template's front matter holds the shared keys; its body opens with the type's summary as a comment."""
    doc_type = DOC_TYPES[name]
    header, _, body = doc_type.template().removeprefix("---\n").partition("\n---\n")
    front_matter = yaml.safe_load(header)
    assert list(front_matter) == ["type", "title", "description"]
    assert front_matter["type"] == name
    assert " ".join(body.split()).startswith(f"<!-- {doc_type.summary} -->")


@pytest.mark.parametrize(
    "text",
    [
        # specs accepts any body, so only the encoding and the line endings are tested.
        f"---\r\ntype: specs\r\n{META.replace(chr(10), chr(13) + chr(10))}---\r\n\r\nBody\r\n",  # Windows line endings
        f"﻿---\ntype: specs\n{META}---\n",  # byte-order mark
        f"---\ntype: specs\n{META}---",  # no trailing newline
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
        (f"---\n{META}---\n", "type-missing", None),
        (f"---\ntype: 3\n{META}---\n", "type-not-text", None),
        (f"---\ntype: recipe\n{META}---\n", "type-unknown", None),
        (f"---\ntype: Glossary\n{META}---\n", "type-unknown", None),
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


def test_missing_metadata_does_not_stop_the_type_checks(tmp_path: Path) -> None:
    """A missing title or description is reported, but the body is still parsed and validated."""
    result = check_file(write(tmp_path, "---\ntype: requirements\n---\n"))
    assert [(finding.kind, finding.code) for finding in result.findings] == [
        ("parse", "title-missing"),
        ("parse", "description-missing"),
        ("validate", "requirements-none"),
    ]
    assert result.validated
    assert not result.ok


class _ParserWithFinding:
    def parse(self, document: Document, metadata: Metadata) -> tuple[None, list[ParserFinding]]:
        return None, [ParserFinding(code="block-broken", message="a block is broken", hint="fix the block")]


class _ParserWithoutFinding:
    def parse(self, document: Document, metadata: Metadata) -> tuple[None, list[ParserFinding]]:
        return None, []


class _ParserRecoveringWithFinding:
    """Reads the document but reports a problem it could work around."""

    def parse(self, document: Document, metadata: Metadata) -> tuple[GlossaryDoc | None, list[ParserFinding]]:
        finding = ParserFinding(code="block-odd", message="a block is odd", hint="tidy the block", line=4)
        return GlossaryDoc(metadata=metadata, document=document, terms=()), [finding]


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
    result = check_file(write(tmp_path, f"---\ntype: glossary\n{META}---\n"))
    # The validator's finding has no line, so it concerns the whole file and comes first.
    assert [(finding.kind, finding.code) for finding in result.findings] == [
        ("validate", "rule-broken"),
        ("parse", "block-odd"),
    ]
    assert len(validator.seen) == 1
    assert result.validated
    assert not result.ok


def test_a_failed_type_parser_skips_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _use_parser(monkeypatch, _ParserWithFinding())
    result = check_file(write(tmp_path, f"---\ntype: glossary\n{META}---\n"))
    assert [finding.code for finding in result.findings] == ["block-broken"]
    assert result.doc_type == "glossary"
    assert not result.validated
    assert not result.ok


def test_a_parser_failing_without_a_finding_stops_the_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A parser that gives up silently is a bug: it must never let a document pass unchecked."""
    _use_parser(monkeypatch, _ParserWithoutFinding())
    with pytest.raises(RuntimeError, match="internal error"):
        check_file(write(tmp_path, f"---\ntype: glossary\n{META}---\n"))


def test_shared_checks_run_even_when_the_type_is_unusable(tmp_path: Path) -> None:
    result = check_file(write(tmp_path, "---\ntype: recipe\ntitle: ''\ndescription: A description.\n---\n"))
    assert [(finding.kind, finding.code) for finding in result.findings] == [
        ("parse", "type-unknown"),
        ("validate", "title-empty"),
    ]
    assert not result.validated


def test_project_reports_requirement_ids_used_in_several_documents(tmp_path: Path) -> None:
    template = DOC_TYPES["requirements"].template()
    documents = {
        "a.md": write(tmp_path, template, "a.md"),
        "b.md": write(tmp_path, template, "b.md"),
        "glossary.md": write(tmp_path, DOC_TYPES["glossary"].template(), "glossary.md"),
    }
    results = check_project(documents)
    assert results["glossary.md"].ok
    for name, other in (("a.md", "b.md"), ("b.md", "a.md")):
        findings = results[name].findings
        assert {finding.code for finding in findings} == {"requirement-id-duplicate"}
        assert len(findings) == 5
        assert f"'LOG-001' is also used at {other}:10" in findings[0].hint
        assert not results[name].ok


def test_findings_are_in_reading_order(tmp_path: Path) -> None:
    """Findings read top to bottom like the file, whichever step found them."""
    text = (
        "---\ntype: requirements\ntitle: A title\n---\n"  # lines 1-4; no description
        "\n"  # 5
        "## A\n"  # 6
        "\n"  # 7
        "The logger logs.\n"  # 8: a validation finding
        "\n"  # 9
        "- Notes: x\n"  # 10: a parse finding
        "<!-- never closed\n"  # 11: a parse finding, found before the one above
    )
    findings = check_file(write(tmp_path, text)).findings
    assert [(finding.kind, finding.code) for finding in findings] == [
        ("parse", "description-missing"),
        ("validate", "statement-shall-missing"),
        ("parse", "requirement-field-unknown"),
        ("parse", "comment-unterminated"),
    ]


def test_project_reports_terms_defined_in_several_glossaries(tmp_path: Path) -> None:
    template = DOC_TYPES["glossary"].template()
    results = check_project({"a.md": write(tmp_path, template, "a.md"), "b.md": write(tmp_path, template, "b.md")})
    for name, other in (("a.md", "b.md"), ("b.md", "a.md")):
        findings = results[name].findings
        assert [finding.code for finding in findings] == ["term-duplicate"] * 4
        assert f"'Hold-up capacitor' is also defined at {other}:9" in findings[0].hint
