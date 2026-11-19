"""The validator for ``overview`` documents.

The blocks of a ``overview`` document are not defined yet, so this validator
accepts every document. Checks shared by every document type belong in
``sks_tool.validators.base``.
"""

from sks_tool.docs.overview.doc import OverviewDoc
from sks_tool.findings import ValidatorFinding


class OverviewValidator:
    """Checks a ``OverviewDoc``."""

    def validate(self, doc: OverviewDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        return []
