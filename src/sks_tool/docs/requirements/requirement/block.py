"""The structure of one requirement.

In a ``requirements`` document, a requirement is written as::

    ## LOG-001

    The logger **shall** sample each accelerometer axis at 1 kHz.

    - Rationale: Vibration analysis needs content up to 400 Hz.

The level-2 heading is its ID, the paragraph under it is its statement, and
the bullet list holds its optional fields.
"""

from dataclasses import dataclass

FIELDS = ("Rationale",)
"""The fields a requirement may have, as written before the ':' of their bullet."""


@dataclass(frozen=True)
class Requirement:
    """One requirement read from its block."""

    id: str
    """The heading text; unique across every document checked together."""
    statement: str
    """What is required, as written; lines are joined with ``\\n`` if it spans several."""
    rationale: str | None
    """Why it is required, or ``None`` if the field is absent."""
    line: int
    """1-based line of the requirement's heading in the file."""
    statement_line: int
    """1-based line where the statement starts."""
    rationale_line: int | None
    """1-based line of the rationale field, or ``None`` if absent."""
