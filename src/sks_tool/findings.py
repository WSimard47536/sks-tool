"""Findings: the problems sks-tool reports about a document.

Every finding states what is wrong (``message``) and how to fix it (``hint``).
There are two kinds, so the reader can tell at a glance what happened:

- ``ParserFinding``: the file could not be read into its structure. It points
  at a line of the raw file.
- ``ValidatorFinding``: the structure was read but breaks a rule. It points at
  a place in the structure (``location``) and, when known, at a line.

``Finding`` itself is only the shared base and cannot be created directly.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class Finding:
    """One problem found in a document."""

    kind: ClassVar[str]
    """How the output labels this kind of finding."""

    code: str
    """Stable identifier of the check, e.g. ``front-matter-missing``."""
    message: str
    """What is wrong."""
    hint: str
    """How to fix it."""

    def __post_init__(self) -> None:
        if type(self) is Finding:
            raise TypeError("Finding is a base class; create a ParserFinding or a ValidatorFinding")
        for name in ("code", "message", "hint"):
            if not getattr(self, name).strip():
                raise ValueError(f"a finding must have a non-empty {name}")


@dataclass(frozen=True, kw_only=True)
class ParserFinding(Finding):
    """A problem that prevented reading the file into its structure."""

    kind: ClassVar[str] = "parse"

    line: int | None = None
    """1-based line in the file, or ``None`` if it concerns the whole file."""


@dataclass(frozen=True, kw_only=True)
class ValidatorFinding(Finding):
    """A rule broken by a structure that was read successfully."""

    kind: ClassVar[str] = "validate"

    location: tuple[str, ...] = ()
    """Where in the structure, outermost first, e.g. ``("requirement REQ-012", "rationale")``.

    Empty when the finding concerns the whole document."""
    line: int | None = None
    """1-based line in the file, or ``None`` if not known."""
