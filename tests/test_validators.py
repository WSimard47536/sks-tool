from pathlib import Path

import pytest

from sks_tool.doctypes import DOC_TYPES
from sks_tool.document import Document
from sks_tool.validators.base import CommonValidator


def make_document(name: str) -> Document:
    return Document(path=Path("doc.md"), front_matter={"type": name}, body="", body_line=4)


def test_common_validator_has_no_checks_yet() -> None:
    assert CommonValidator().validate(make_document("glossary")) == []


@pytest.mark.parametrize("name", list(DOC_TYPES))
def test_type_validator_accepts_any_structure_while_blocks_are_undefined(name: str) -> None:
    doc_type = DOC_TYPES[name]
    structure, _ = doc_type.parser.parse(make_document(name))
    assert doc_type.validator.validate(structure) == []
