"""The structure of a ``specs`` document.

The blocks of a ``specs`` document are not defined yet, so the structure only
holds its metadata and the document it was read from. Add its blocks here,
each in its own subpackage.
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.document import Document


@dataclass(frozen=True)
class SpecsDoc:
    """A ``specs`` document read into its structure."""

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
