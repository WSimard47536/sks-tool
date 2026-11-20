"""The structure shared by requirements and specs.

A requirement and a spec are written the same way::

    ## LOG-004

    Type: Functional

    Status: Underway

    The logger **shall** close the current log file within 50 ms of a power-loss signal.

    - Rationale: The hold-up capacitor keeps the logger powered for 80 ms after power loss.

    Acceptance criteria:

    - [x] The bench test closes the file within 50 ms in 100 out of 100 power cuts.
    - [ ] The flight test log shows no truncated file after a power loss.

In order: the ID heading, the type line, the status line (each followed by a
blank line), the statement, the fields, then the acceptance criteria as a
checkbox list. A spec may end with a diagram.
"""

from dataclasses import dataclass
from enum import StrEnum

TYPE_LABEL = "Type"
"""The label of the type line, as written before its ':'."""
STATUS_LABEL = "Status"
"""The label of the status line, as written before its ':'."""
RATIONALE = "Rationale"
"""The rationale field's label."""
CRITERIA_LABEL = "Acceptance criteria:"
"""The line that opens the acceptance criteria list, as written."""


class Status(StrEnum):
    """How far a requirement or spec is from being met, each value as written after ``Status:``."""

    PENDING = "Pending"
    """Work has not started."""
    UNFULFILLED = "Unfulfilled"
    """The current implementation is not satisfactory."""
    UNDERWAY = "Underway"
    """Work is in progress."""
    FULFILLED = "Fulfilled"
    """Every acceptance criterion is met."""


@dataclass(frozen=True)
class AcceptanceCriterion:
    """One checkbox of the acceptance criteria list: ``- [ ] <text>`` or ``- [x] <text>``."""

    text: str
    checked: bool
    line: int
    """1-based line of the checkbox."""
