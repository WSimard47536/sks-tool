"""The validator for ``specs`` documents.

The blocks of a ``specs`` document are not defined yet, so this validator
accepts every document. Checks shared by every document type belong in
``sks_tool.validators.base``.
"""

from sks_tool.docs.specs.doc import SpecsDoc
from sks_tool.findings import ValidatorFinding


class SpecsValidator:
    """Checks a ``SpecsDoc``."""

    def validate(self, doc: SpecsDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        return []
