"""The validator for the rules that span documents.

Some rules cannot be checked one document at a time, because they concern
every document checked together (the documents listed in ``sks.toml``):

- requirement IDs must be unique;
- glossary terms must be unique, ignoring case.

``ProjectValidator`` runs after every document has been parsed and validated
on its own, and reports each finding against the document it concerns.
"""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from sks_tool.docs.glossary.doc import GlossaryDoc
from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.findings import ValidatorFinding
from sks_tool.validators.glossary.term.validator import term_location


@dataclass(frozen=True)
class _Use:
    """One place where a name that must be unique is used."""

    document: str
    line: int
    text: str
    """The name as written there."""
    location: str
    """How findings name the entry, e.g. ``requirement LOG-001``."""


class ProjectValidator:
    """Checks the rules that span the documents checked together."""

    def validate(self, structures: Mapping[str, object]) -> dict[str, list[ValidatorFinding]]:
        """Return the findings for each document, keyed like ``structures``.

        ``structures`` maps each document's name, as shown in the output, to
        its parsed structure. Documents without findings are left out.
        """
        requirement_ids: dict[str, list[_Use]] = defaultdict(list)
        terms: dict[str, list[_Use]] = defaultdict(list)
        for name, structure in structures.items():
            if isinstance(structure, RequirementsDoc):
                for requirement in structure.requirements:
                    requirement_ids[requirement.id].append(
                        _Use(name, requirement.line, requirement.id, f"requirement {requirement.id}")
                    )
            elif isinstance(structure, GlossaryDoc):
                for term in structure.terms:
                    terms[term.term.casefold()].append(_Use(name, term.line, term.term, term_location(term)))

        findings: dict[str, list[ValidatorFinding]] = defaultdict(list)
        for uses in requirement_ids.values():
            _report_duplicates(
                uses,
                findings,
                code="requirement-id-duplicate",
                message="the ID is used by {count} requirements",
                hint="give each requirement its own ID; '{text}' is also used at {others}",
            )
        for uses in terms.values():
            _report_duplicates(
                uses,
                findings,
                code="term-duplicate",
                message="the term is defined {count} times (ignoring case)",
                hint="define each term once; '{text}' is also defined at {others}",
            )
        return dict(findings)


def _report_duplicates(
    uses: list[_Use], findings: dict[str, list[ValidatorFinding]], *, code: str, message: str, hint: str
) -> None:
    """Report a name used more than once at every place it is used, naming the other places."""
    if len(uses) < 2:
        return
    for use in uses:
        others = ", ".join(f"{other.document}:{other.line}" for other in uses if other is not use)
        findings[use.document].append(
            ValidatorFinding(
                code=code,
                message=message.format(count=len(uses)),
                hint=hint.format(text=use.text, others=others),
                location=(use.location,),
                line=use.line,
            )
        )
