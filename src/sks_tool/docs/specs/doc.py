"""The structure of a ``specs`` document.

A ``specs`` document is a sequence of specs and nothing else; blank lines and
``<!-- comments -->`` may appear between them. Its title and description are
in the front matter.
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.docs.specs.spec.block import Spec
from sks_tool.document import Document


@dataclass(frozen=True)
class SpecsDoc:
    """A ``specs`` document read into its structure."""

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
    specs: tuple[Spec, ...]
    """The specs that could be read, in file order."""
