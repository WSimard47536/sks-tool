"""The structure of a ``requirements`` document.

A ``requirements`` document is a sequence of requirements and nothing else;
blank lines and ``<!-- comments -->`` may appear between them. Its title and
description are in the front matter.
"""

from dataclasses import dataclass

from sks_tool.docs.base import Metadata
from sks_tool.docs.requirements.requirement.block import Requirement
from sks_tool.document import Document


@dataclass(frozen=True)
class RequirementsDoc:
    """A ``requirements`` document read into its structure."""

    metadata: Metadata
    document: Document
    """The document this structure was read from."""
    requirements: tuple[Requirement, ...]
    """The requirements that could be read, in file order."""
