"""The validator for ``requirements`` documents.

A ``requirements`` document must contain at least one requirement; each
requirement is checked by ``RequirementValidator``. Uniqueness of the IDs
spans documents, so it is checked by ``sks_tool.validators.project``.
"""

from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.requirements.requirement.validator import RequirementValidator


class RequirementsValidator:
    """Checks a ``RequirementsDoc``."""

    def validate(self, doc: RequirementsDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        if not doc.requirements:
            return [
                ValidatorFinding(
                    code="requirements-none",
                    message="the document contains no requirement",
                    hint="add one: a '## <ID>' heading, then its statement as the paragraph under it",
                )
            ]
        requirement_validator = RequirementValidator()
        findings: list[ValidatorFinding] = []
        for requirement in doc.requirements:
            findings += requirement_validator.validate(requirement)
        return findings
