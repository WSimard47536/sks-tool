import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sks_tool import pipeline
from sks_tool.cli import app
from sks_tool.doctypes import DOC_TYPES
from sks_tool.findings import ValidatorFinding

runner = CliRunner()


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty folder that is also the current directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_list(project: Path, *paths: str) -> None:
    text = "".join(f'[[documents]]\npath = "{path}"\n\n' for path in paths)
    (project / "sks.toml").write_bytes(text.encode("utf-8"))


def test_types_lists_every_type() -> None:
    result = runner.invoke(app, ["types"])
    assert result.exit_code == 0
    assert [line.split()[0] for line in result.output.splitlines()] == list(DOC_TYPES)


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_new_creates_a_document_that_validates(project: Path, name: str) -> None:
    result = runner.invoke(app, ["new", name, "docs/sub/doc.md"])
    assert result.exit_code == 0
    created = project / "docs" / "sub" / "doc.md"
    # Byte-for-byte the template, with "\n" line endings on every platform.
    assert created.read_bytes() == DOC_TYPES[name].template().encode()
    assert created.read_bytes().startswith(f"---\ntype: {name}\n".encode())
    assert b"\r" not in created.read_bytes()

    write_list(project, "docs/sub/doc.md")
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert f"docs/sub/doc.md: ok ({name})" in result.output


def test_new_rejects_unknown_type(project: Path) -> None:
    result = runner.invoke(app, ["new", "recipe", "doc.md"])
    assert result.exit_code == 2
    assert not (project / "doc.md").exists()


def test_new_does_not_overwrite(project: Path) -> None:
    (project / "doc.md").write_text("keep me", encoding="utf-8")
    result = runner.invoke(app, ["new", "glossary", "doc.md"])
    assert result.exit_code == 2
    assert (project / "doc.md").read_text(encoding="utf-8") == "keep me"


def test_validate_reports_failures_as_text(project: Path) -> None:
    runner.invoke(app, ["new", "glossary", "good.md"])
    (project / "bad.md").write_bytes(b"# No front matter\n")
    write_list(project, "good.md", "bad.md", "absent.md")

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert "good.md: ok (glossary)" in lines
    assert "bad.md:1: parse: the file does not start with a front matter block [front-matter-missing]" in lines
    assert "    fix: make the first line '---', then 'type: <type>', then a closing '---'" in lines
    assert "bad.md: type-specific validation skipped until the parse findings are fixed" in lines
    assert "absent.md: parse: file does not exist [file-not-found]" in lines
    assert "absent.md: type-specific validation skipped until the parse findings are fixed" in lines
    assert "3 document(s) checked: 1 ok, 2 failed (2 parse finding(s), 0 validation finding(s), 2 skipped)" in lines


def test_validate_reports_validator_findings_with_their_location(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectingValidator:
        def validate(self, doc: object) -> list[ValidatorFinding]:
            return [
                ValidatorFinding(
                    code="rationale-empty",
                    message="is empty",
                    hint="state why this requirement exists",
                    location=("requirement REQ-012", "rationale"),
                    line=7,
                )
            ]

    patched = {name: replace(doc_type, validator=RejectingValidator()) for name, doc_type in DOC_TYPES.items()}
    monkeypatch.setattr(pipeline, "DOC_TYPES", patched)
    runner.invoke(app, ["new", "requirements", "reqs.md"])
    write_list(project, "reqs.md")

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert "reqs.md:7: validate: requirement REQ-012 › rationale: is empty [rationale-empty]" in lines
    assert "    fix: state why this requirement exists" in lines
    assert not any("validation skipped" in line for line in lines)
    assert "1 document(s) checked: 0 ok, 1 failed (0 parse finding(s), 1 validation finding(s), 0 skipped)" in lines

    result = runner.invoke(app, ["validate", "--json"])
    document = json.loads(result.stdout)["documents"][0]
    assert (document["ok"], document["validated"]) == (False, True)
    assert document["findings"] == [
        {
            "kind": "validate",
            "code": "rationale-empty",
            "message": "is empty",
            "hint": "state why this requirement exists",
            "line": 7,
            "location": ["requirement REQ-012", "rationale"],
        }
    ]


def test_validate_reports_failures_as_json(project: Path) -> None:
    runner.invoke(app, ["new", "glossary", "good.md"])
    (project / "bad.md").write_bytes(b"---\ntype: recipe\ntitle: Bad\ndescription: A bad document.\n---\n")
    write_list(project, "good.md", "bad.md")

    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error"] is None
    assert payload["documents"][0] == {
        "path": "good.md",
        "type": "glossary",
        "ok": True,
        "validated": True,
        "findings": [],
    }
    bad = payload["documents"][1]
    assert (bad["path"], bad["type"], bad["ok"], bad["validated"]) == ("bad.md", None, False, False)
    assert bad["findings"] == [
        {
            "kind": "parse",
            "code": "type-unknown",
            "message": "unknown type 'recipe'",
            "hint": "set 'type' to one of: requirements, specs, overview, glossary (lowercase, exact)",
            "line": None,
            "location": None,
        }
    ]


def test_validate_with_an_empty_list_passes(project: Path) -> None:
    write_list(project)
    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"ok": True, "error": None, "documents": []}


def test_validate_without_a_list_fails(project: Path) -> None:
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 2

    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "not found" in payload["error"]


def test_validate_resolves_paths_relative_to_the_list(project: Path) -> None:
    elsewhere = project / "elsewhere"
    runner.invoke(app, ["new", "overview", "elsewhere/docs/overview.md"])
    write_list(elsewhere, "docs/overview.md")

    result = runner.invoke(app, ["validate", "--config", "elsewhere/sks.toml"])
    assert result.exit_code == 0
    assert "docs/overview.md: ok (overview)" in result.output


def test_redirected_output_is_utf8_whatever_the_system_code_page(project: Path) -> None:
    """A path the code page cannot encode must print, not crash the tool."""
    write_list(project, "文.md")
    env = {**os.environ, "PYTHONIOENCODING": "cp437"}
    completed = subprocess.run(
        [sys.executable, "-m", "sks_tool.cli", "validate"], cwd=project, env=env, capture_output=True, check=False
    )
    assert completed.returncode == 1, completed.stderr.decode("utf-8", "replace")
    assert "文.md: parse: file does not exist [file-not-found]" in completed.stdout.decode("utf-8").splitlines()


def test_validate_reports_ids_used_in_two_documents(project: Path) -> None:
    """Two documents created from the template keep its example IDs until edited: both are flagged."""
    runner.invoke(app, ["new", "requirements", "a.md"])
    runner.invoke(app, ["new", "requirements", "b.md"])
    write_list(project, "a.md", "b.md")

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert "a.md:10: validate: requirement LOG-001: the ID is used by 2 requirements [requirement-id-duplicate]" in lines
    assert "    fix: give each requirement its own ID; 'LOG-001' is also used at b.md:10" in lines
    assert "    fix: give each requirement its own ID; 'LOG-001' is also used at a.md:10" in lines
    assert "2 document(s) checked: 0 ok, 2 failed (0 parse finding(s), 10 validation finding(s), 0 skipped)" in lines

    result = runner.invoke(app, ["validate", "--json"])
    documents = json.loads(result.stdout)["documents"]
    assert [(document["ok"], document["validated"], len(document["findings"])) for document in documents] == [
        (False, True, 5),
        (False, True, 5),
    ]
    assert documents[1]["findings"][0]["location"] == ["requirement LOG-001"]
