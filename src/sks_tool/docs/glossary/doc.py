"""The structure of a ``glossary`` document.

The blocks of a ``glossary`` document are not defined yet, so the structure only
holds its metadata and the document it was read from. Add its blocks here,
each in its own subpackage.
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.document import Document


@dataclass(frozen=True)
class GlossaryDoc:
    """A ``glossary`` document read into its structure."""

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
