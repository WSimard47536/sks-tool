"""The validator for ``glossary`` documents.

A ``glossary`` document must contain at least one term, and its terms must
be in alphabetical order, ignoring case; each term is checked by
``TermValidator``. Uniqueness of the terms spans documents, so it is checked
by ``sks_tool.validators.project``.

The order compares characters as written, after ignoring case: a space sorts
before letters ("Log file" before "Logger"), and accented letters after "z".
This gives the same answer on every machine, unlike a locale-aware sort.
"""

from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.glossary.term.validator import TermValidator, term_location


class GlossaryValidator:
    """Checks a ``GlossaryDoc``."""

    def validate(self, doc: GlossaryDoc) -> list[ValidatorFinding]:
        """Return the rules the document breaks."""
        if not doc.terms:
            return [
                ValidatorFinding(
                    code="glossary-none",
                    message="the document contains no term",
                    hint="add one: a '## <term>' heading, then its definition as the paragraph under it",
                )
            ]
        term_validator = TermValidator()
        findings: list[ValidatorFinding] = []
        for previous, term in zip((None, *doc.terms), doc.terms, strict=False):
            findings += term_validator.validate(term)
            # Each term is compared with the one above it, so a single misplaced
            # term gives a single finding.
            if previous is not None and term.term.casefold() < previous.term.casefold():
                findings.append(
                    ValidatorFinding(
                        code="term-out-of-order",
                        message=f"comes after '{previous.term}'",
                        hint=f"sort the terms alphabetically; '{term.term}' belongs before '{previous.term}'",
                        location=(term_location(term),),
                        line=term.line,
                    )
                )
        return findings
