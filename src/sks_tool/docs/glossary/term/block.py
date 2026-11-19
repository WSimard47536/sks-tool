"""The structure of one glossary term.

In a ``glossary`` document, a term is written as::

    ## Log file

    A file on the logger's non-volatile memory holding the samples of one power-on session.

The level-2 heading is the term (a word or a short expression), and the
paragraph under it is what the term means in the project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    """One term read from its block."""

    term: str
    """The heading text; unique, ignoring case, across every glossary checked together."""
    definition: str
    """What the term means, as written; lines are joined with ``\\n`` if it spans several."""
    line: int
    """1-based line of the term's heading in the file."""
    definition_line: int
    """1-based line where the definition starts."""
