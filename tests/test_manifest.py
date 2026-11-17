from pathlib import Path

import pytest

from sks_tool.manifest import ManifestError, load_manifest


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "sks.toml"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_paths_are_returned_in_order(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        '# comment\n[[documents]]\npath = "docs/requirements.md"\n\n[[documents]]\npath = "docs/glossary.md"\n',
    )
    assert load_manifest(path) == ["docs/requirements.md", "docs/glossary.md"]


def test_empty_list_is_allowed(tmp_path: Path) -> None:
    assert load_manifest(write(tmp_path, "")) == []


def test_missing_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="not found"):
        load_manifest(tmp_path / "sks.toml")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[[documents]\n", "not valid TOML"),
        ('[[document]]\npath = "a.md"\n', "unknown key"),
        ('documents = "a.md"\n', r"\[\[documents\]\] entries"),
        ('documents = ["a.md"]\n', r"\[\[documents\]\] entries"),
        ('[[documents]]\npaht = "a.md"\n', "unknown key"),
        ('[[documents]]\npath = "a.md"\ntype = "glossary"\n', "unknown key"),
        ("[[documents]]\n", "non-empty string"),
        ("[[documents]]\npath = 3\n", "non-empty string"),
        ('[[documents]]\npath = " "\n', "non-empty string"),
        ('[[documents]]\npath = "a.md"\n\n[[documents]]\npath = "a.md"\n', "more than once"),
    ],
)
def test_malformed_lists_are_rejected(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(ManifestError, match=message):
        load_manifest(write(tmp_path, text))
