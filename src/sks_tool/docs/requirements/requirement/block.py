"""The structure of one requirement.

In a ``requirements`` document, a requirement is written as::

    ## LOG-004

    Type: Functional

    The logger **shall** close the current log file within 50 ms of a power-loss signal.

    - Rationale: The hold-up capacitor keeps the logger powered for 80 ms after power loss.

The level-2 heading is its ID. The first line under it states its type, the
paragraph after that is its statement, and the bullet list holds its
optional fields.
"""

from dataclasses import dataclass
from enum import StrEnum

TYPE_LABEL = "Type"
"""The label of the type line, as written before its ':'."""

FIELDS = ("Rationale",)
"""The fields a requirement may have, as written before the ':' of their bullet."""


class RequirementType(StrEnum):
    """The kinds of requirement, each value as written after ``Type:``."""

    BUSINESS = "Business"
    """What the system must do to fulfil its purpose."""
    FUNCTIONAL = "Functional"
    """What the system must do to fulfil the business requirements."""
    NON_FUNCTIONAL = "Non-functional"
    """How the system must do it: safety standards, performance, and so on."""


@dataclass(frozen=True)
class Requirement:
    """One requirement read from its block."""

    id: str
    """The heading text; unique across every document checked together."""
    type: str | None
    """The type as written, or ``None`` if the type line is missing; the
    validator checks it is a ``RequirementType``."""
    statement: str
    """What is required, as written; lines are joined with ``\\n`` if it spans several."""
    rationale: str | None
    """Why it is required, or ``None`` if the field is absent."""
    line: int
    """1-based line of the requirement's heading in the file."""
    type_line: int | None
    """1-based line of the type line, or ``None`` if absent."""
    statement_line: int
    """1-based line where the statement starts."""
    rationale_line: int | None
    """1-based line of the rationale field, or ``None`` if absent."""
