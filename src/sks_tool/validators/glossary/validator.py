"""The validator for ``glossary`` documents.

The blocks of a ``glossary`` document are not defined yet, so this validator
accepts every document. Checks shared by every document type belong in
``sks_tool.validators.base``.
"""

from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.findings import ValidatorFinding


class GlossaryValidator:
    """Checks a ``GlossaryDoc``."""

    def validate(self, doc: GlossaryDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        return []
