"""The validator for ``requirements`` documents.

The blocks of a ``requirements`` document are not defined yet, so this validator
accepts every document. Checks shared by every document type belong in
``sks_tool.validators.base``.
"""

from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.findings import ValidatorFinding


class RequirementsValidator:
    """Checks a ``RequirementsDoc``."""

    def validate(self, doc: RequirementsDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        return []
