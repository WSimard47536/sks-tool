"""The structure of a ``glossary`` document.

A ``glossary`` document is a sequence of terms in alphabetical order, and
nothing else; blank lines and ``<!-- comments -->`` may appear between them.
Its title and description are in the front matter.
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.docs.glossary.term.block import Term
from sks_tool.document import Document


@dataclass(frozen=True)
class GlossaryDoc:
    """A ``glossary`` document read into its structure."""

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
    terms: tuple[Term, ...]
    """The terms that could be read, in file order."""
