"""The registry of SKS document types.

Each type has a name (the value of ``type:`` in a document's front matter), a
summary of what the document is for, a template in
``sks_tool/templates/<name>.md`` and its own parser in
``sks_tool/parsers/<name>.py``. To add a type, add those two files and an
entry in ``DOC_TYPES`` below. Each template repeats its type's summary as a
guidance comment; a test keeps the two in step.
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import resources

from sks_tool.document import Document, Issue
from sks_tool.parsers import glossary, overview, requirements, specs


@dataclass(frozen=True)
class DocType:
    """One kind of SKS document."""

    name: str
    summary: str
    validate: Callable[[Document], list[Issue]]

    def template(self) -> str:
        """Return the text a new document of this type starts from."""
        return resources.files("sks_tool").joinpath("templates", f"{self.name}.md").read_text(encoding="utf-8")


DOC_TYPES: dict[str, DocType] = {
    doc_type.name: doc_type
    for doc_type in (
        DocType(
            "requirements",
            "What the project must satisfy; if one is not met, the project misses its objectives, "
            "does not work, or is unsafe.",
            requirements.validate,
        ),
        DocType("specs", "How it is built: diagrams, the design choices made, and why.", specs.validate),
        DocType("overview", "What the project is, what it does and why, with a system diagram.", overview.validate),
        DocType("glossary", "What the project's terms mean.", glossary.validate),
    )
}
