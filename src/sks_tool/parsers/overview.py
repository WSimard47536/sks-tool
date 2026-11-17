"""Parser for ``overview`` documents.

The blocks of a ``overview`` document are not defined yet, so this parser
accepts every document. Add the checks specific to this type here; checks
shared by every document type belong in ``sks_tool.parsers.common``.
"""

from sks_tool.document import Document, Issue


def validate(document: Document) -> list[Issue]:
    """Return the problems found in a ``overview`` document."""
    return []
