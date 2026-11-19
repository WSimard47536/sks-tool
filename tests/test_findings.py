import pytest

from sks_tool.findings import Finding, ParserFinding, ValidatorFinding


def test_the_two_kinds_are_labelled_differently() -> None:
    assert ParserFinding.kind == "parse"
    assert ValidatorFinding.kind == "validate"


def test_the_base_class_cannot_be_created() -> None:
    with pytest.raises(TypeError):
        Finding(code="x", message="x", hint="x")


@pytest.mark.parametrize("empty", ["code", "message", "hint"])
@pytest.mark.parametrize("cls", [ParserFinding, ValidatorFinding])
def test_every_field_must_be_filled_in(cls: type[Finding], empty: str) -> None:
    """A finding that does not say what is wrong and how to fix it is not actionable."""
    fields = {"code": "x", "message": "x", "hint": "x", empty: "  "}
    with pytest.raises(ValueError, match=empty):
        cls(**fields)
