"""The ``Validator`` interface, and the root validator shared by every document.

A validator checks a structure that was read successfully and returns the
rules it breaks; an empty list means the structure is valid.

``CommonValidator`` runs the checks shared by every document type. None are
defined yet; add them to ``CommonValidator.validate``.
"""

from typing import Protocol

from sks_tool.document import Document
from sks_tool.findings import ValidatorFinding


class Validator[T](Protocol):
    """Checks a structure of type ``T``."""

    def validate(self, target: T, /) -> list[ValidatorFinding]:
        """Return the rules ``target`` breaks."""
        ...


class CommonValidator:
    """Runs the checks shared by every document type."""

    def validate(self, document: Document) -> list[ValidatorFinding]:
        """Return the shared rules the document breaks."""
        return []
