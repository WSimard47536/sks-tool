"""The validator for one glossary term.

The term is at most 100 characters long. The definition fits on one line and
is at most 200 characters long. Both are counted as written.

Uniqueness of the terms spans documents, so it is checked by
``sks_tool.validators.project``; their order is checked by
``GlossaryValidator``.
"""

from sks_tool.docs.glossary.term.block import Term
from sks_tool.findings import ValidatorFinding

TERM_MAX_CHARACTERS = 100
DEFINITION_MAX_CHARACTERS = 200


def term_location(term: Term) -> str:
    """How findings name a term."""
    return f"term '{term.term}'"


class TermValidator:
    """Checks a ``Term``."""

    def validate(self, term: Term) -> list[ValidatorFinding]:
        """Return the rules the term breaks."""
        findings: list[ValidatorFinding] = []
        if len(term.term) > TERM_MAX_CHARACTERS:
            findings.append(
                ValidatorFinding(
                    code="term-too-long",
                    message=f"is {len(term.term)} characters long; the limit is {TERM_MAX_CHARACTERS}",
                    hint="a term is a word or a short expression: shorten it",
                    location=(term_location(term),),
                    line=term.line,
                )
            )

        def definition_finding(code: str, message: str, hint: str) -> ValidatorFinding:
            return ValidatorFinding(
                code=code,
                message=message,
                hint=hint,
                location=(term_location(term), "definition"),
                line=term.definition_line,
            )

        line_count = term.definition.count("\n") + 1
        if line_count > 1:
            findings.append(
                definition_finding(
                    "definition-not-one-line",
                    f"spans {line_count} lines",
                    "write the definition on a single line",
                )
            )
        length = len(" ".join(term.definition.split("\n")))
        if length > DEFINITION_MAX_CHARACTERS:
            findings.append(
                definition_finding(
                    "definition-too-long",
                    f"is {length} characters long; the limit is {DEFINITION_MAX_CHARACTERS}",
                    "shorten it to what the term means in the project",
                )
            )
        return findings
