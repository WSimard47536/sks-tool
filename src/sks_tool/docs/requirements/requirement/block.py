"""The structure of one requirement.

A requirement is written as described in ``sks_tool.docs.req_spec_shared``;
its type is one of ``RequirementType``.
"""

from dataclasses import dataclass
from enum import StrEnum

from sks_tool.docs.req_spec_shared import RATIONALE, AcceptanceCriterion

FIELDS = (RATIONALE,)
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
    """One requirement read from its block.

    The type and the status are kept as written, or ``None`` if their line is
    missing; the validator checks them against ``RequirementType`` and
    ``Status``.
    """

    id: str
    """The heading text; unique across every requirement and spec checked together."""
    type: str | None
    status: str | None
    statement: str
    """What is required, as written; lines are joined with ``\\n`` if it spans several."""
    rationale: str | None
    """Why it is required, or ``None`` if the field is absent."""
    criteria: tuple[AcceptanceCriterion, ...]
    line: int
    """1-based line of the requirement's heading in the file."""
    type_line: int | None
    status_line: int | None
    statement_line: int
    rationale_line: int | None
