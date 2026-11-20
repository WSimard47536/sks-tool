"""The registry of SKS document types.

Each type has a name (the value of ``type:`` in a document's front matter), a
summary of what the document is for, a template in
``sks_tool/templates/<name>.md``, and three packages that follow the same
layout:

- ``sks_tool/docs/<name>/doc.py``: the structure of the document;
- ``sks_tool/parsers/<name>/parser.py``: reads a document into that structure;
- ``sks_tool/validators/<name>/validator.py``: checks that structure.

To add a type, add those files and an entry in ``DOC_TYPES`` below. Each
template repeats its type's summary as a guidance comment; a test keeps the
two in step.
"""

from dataclasses import dataclass
from importlib import resources
from typing import Any

from sks_tool.parsers.base import Parser
from sks_tool.parsers.glossary.parser import GlossaryParser
from sks_tool.parsers.overview.parser import OverviewParser
from sks_tool.parsers.requirements.parser import RequirementsParser
from sks_tool.parsers.specs.parser import SpecsParser
from sks_tool.validators.base import Validator
from sks_tool.validators.glossary.validator import GlossaryValidator
from sks_tool.validators.overview.validator import OverviewValidator
from sks_tool.validators.requirements.validator import RequirementsValidator
from sks_tool.validators.specs.validator import SpecsValidator


@dataclass(frozen=True)
class DocType[T]:
    """One kind of SKS document.

    ``T`` is the structure of the document: the type checker rejects an entry
    whose parser produces something other than what its validator checks.
    """

    name: str
    summary: str
    parser: Parser[T]
    validator: Validator[T]
    companions: tuple[str, ...] = ()
    """Files ``new`` creates next to the document, from ``sks_tool/templates/<file>``,
    such as the diagram an overview shows."""

    def template(self) -> str:
        """Return the text a new document of this type starts from."""
        return resources.files("sks_tool").joinpath("templates", f"{self.name}.md").read_text(encoding="utf-8")

    def companion(self, file_name: str) -> bytes:
        """Return the content of one of the ``companions`` files."""
        return resources.files("sks_tool").joinpath("templates", file_name).read_bytes()


_REQUIREMENTS = DocType(
    "requirements",
    "What the project must satisfy; if one is not met, the project misses its objectives, does not work, or is unsafe.",
    RequirementsParser(),
    RequirementsValidator(),
)
_SPECS = DocType(
    "specs",
    "How it is built: diagrams, the design choices made, and why.",
    SpecsParser(),
    SpecsValidator(),
)
_OVERVIEW = DocType(
    "overview",
    "What the project is, what it does and why, with a system diagram.",
    OverviewParser(),
    OverviewValidator(),
    companions=("system_diagram.drawio.svg",),
)
_GLOSSARY = DocType(
    "glossary",
    "What the project's terms mean.",
    GlossaryParser(),
    GlossaryValidator(),
)

# Each entry is built above without a type annotation so the type checker
# infers its structure from the parser and the validator, and rejects a
# mismatch; annotating it as DocType[Any] would hide one.
DOC_TYPES: dict[str, DocType[Any]] = {doc_type.name: doc_type for doc_type in (_REQUIREMENTS, _SPECS, _OVERVIEW, _GLOSSARY)}
