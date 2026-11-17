import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sks_tool.cli import app
from sks_tool.doctypes import DOC_TYPES

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
    assert created.read_bytes().startswith(f"---\ntype: {name}\n---\n".encode())
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
    assert "good.md: ok (glossary)" in result.output
    assert "bad.md:1: " in result.output
    assert "[front-matter-missing]" in result.output
    assert "absent.md: file does not exist [file-not-found]" in result.output
    assert "3 document(s) checked: 1 ok, 2 failed (2 issue(s))" in result.output


def test_validate_reports_failures_as_json(project: Path) -> None:
    runner.invoke(app, ["new", "glossary", "good.md"])
    (project / "bad.md").write_bytes(b"---\ntype: recipe\n---\n")
    write_list(project, "good.md", "bad.md")

    result = runner.invoke(app, ["validate", "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error"] is None
    assert payload["documents"][0] == {"path": "good.md", "type": "glossary", "ok": True, "issues": []}
    bad = payload["documents"][1]
    assert (bad["path"], bad["type"], bad["ok"]) == ("bad.md", None, False)
    assert [(issue["code"], issue["line"]) for issue in bad["issues"]] == [("type-unknown", None)]


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
