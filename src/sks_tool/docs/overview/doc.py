"""The structure of a ``overview`` document.

The blocks of a ``overview`` document are not defined yet, so the structure only
holds the document it was read from. Add its blocks here, each in its own
subpackage.
"""

from dataclasses import dataclass

from sks_tool.document import Document


@dataclass(frozen=True)
class OverviewDoc:
    """A ``overview`` document read into its structure."""

    document: Document
    """The document this structure was read from."""
