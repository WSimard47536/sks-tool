"""The validator for the rules that span documents.

Some rules cannot be checked one document at a time: requirement IDs must be
unique across every document checked together (the documents listed in
``sks.toml``). ``ProjectValidator`` runs after every document has been
parsed and validated on its own, and reports each finding against the
document it concerns.
"""

from collections import defaultdict
from collections.abc import Mapping

from sks_tool.docs.requirements.doc import RequirementsDoc
from sks_tool.findings import ValidatorFinding


class ProjectValidator:
    """Checks the rules that span the documents checked together."""

    def validate(self, structures: Mapping[str, object]) -> dict[str, list[ValidatorFinding]]:
        """Return the findings for each document, keyed like ``structures``.

        ``structures`` maps each document's name, as shown in the output, to
        its parsed structure. Documents without findings are left out.
        """
        findings: dict[str, list[ValidatorFinding]] = defaultdict(list)
        uses: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for name, structure in structures.items():
            if isinstance(structure, RequirementsDoc):
                for requirement in structure.requirements:
                    uses[requirement.id].append((name, requirement.line))

        for requirement_id, places in uses.items():
            if len(places) < 2:
                continue
            for name, line in places:
                others = ", ".join(
                    f"{other}:{other_line}" for other, other_line in places if (other, other_line) != (name, line)
                )
                findings[name].append(
                    ValidatorFinding(
                        code="requirement-id-duplicate",
                        message=f"the ID is used by {len(places)} requirements",
                        hint=f"give each requirement its own ID; '{requirement_id}' is also used at {others}",
                        location=(f"requirement {requirement_id}",),
                        line=line,
                    )
                )
        return dict(findings)
