"""The validator for ``specs`` documents.

A ``specs`` document must contain at least one spec; each spec is checked by
``SpecValidator``. Uniqueness of the IDs spans documents, and requirements,
so it is checked by ``sks_tool.validators.project``.
"""

from sks_tool.docs.specs.doc import SpecsDoc
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.specs.spec.validator import SpecValidator


class SpecsValidator:
    """Checks a ``SpecsDoc``."""

    def validate(self, doc: SpecsDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        if not doc.specs:
            return [
                ValidatorFinding(
                    code="specs-none",
                    message="the document contains no spec",
                    hint="add one: a '## <ID>' heading, then its type, status, decision, rationale and criteria",
                )
            ]
        spec_validator = SpecValidator(doc.document.path.parent)
        findings: list[ValidatorFinding] = []
        for spec in doc.specs:
            findings += spec_validator.validate(spec)
        return findings
