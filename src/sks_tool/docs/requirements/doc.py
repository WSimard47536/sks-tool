"""The structure of a ``requirements`` document.

The blocks of a ``requirements`` document are not defined yet, so the structure only
holds the document it was read from. Add its blocks here, each in its own
subpackage.
"""

from dataclasses import dataclass

from sks_tool.document import Document


@dataclass(frozen=True)
class RequirementsDoc:
    """A ``requirements`` document read into its structure."""

    document: Document
    """The document this structure was read from."""
