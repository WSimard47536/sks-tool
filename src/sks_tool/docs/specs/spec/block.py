"""The structure of one spec.

A spec records a decision, "we do it this way, and this is why": the
information that would not go in the code's own documentation. It is
written as described in ``sks_tool.docs.req_spec_shared``, with a required
rationale, and may end with a diagram whose file is named after the spec's
ID::

    ## LOG-S-001

    Type: Non-functional

    Status: Fulfilled

    The logger writes samples to a ring buffer in RAM and flushes it to flash every second.

    - Rationale: Flash writes are slow and wear the memory; batching keeps up with 1 kHz sampling.

    Acceptance criteria:

    - [x] The buffer never overflows at 1 kHz on all axes in the bench test.

    ![Ring buffer design](LOG-S-001.drawio.svg)
"""

from dataclasses import dataclass
from enum import StrEnum

from sks_tool.docs.diagram import Diagram
from sks_tool.docs.req_spec_shared import RATIONALE, AcceptanceCriterion

FIELDS = (RATIONALE,)
"""The fields a spec may have, as written before the ':' of their bullet; the rationale is required."""


class SpecType(StrEnum):
    """The kinds of spec, each value as written after ``Type:``. Specs have no business type."""

    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional"


@dataclass(frozen=True)
class Spec:
    """One spec read from its block.

    The type and the status are kept as written, or ``None`` if their line is
    missing; the validator checks them against ``SpecType`` and ``Status``.
    """

    id: str
    """The heading text; unique across every requirement and spec checked together."""
    type: str | None
    status: str | None
    statement: str
    """The decision, as written; lines are joined with ``\\n`` if it spans several."""
    rationale: str | None
    """Why it was decided, or ``None`` if the field is missing (already reported by the parser)."""
    criteria: tuple[AcceptanceCriterion, ...]
    diagram: Diagram | None
    line: int
    """1-based line of the spec's heading in the file."""
    type_line: int | None
    status_line: int | None
    statement_line: int
    rationale_line: int | None
