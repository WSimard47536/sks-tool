"""The metadata shared by every document: the keys of its front matter.

Every SKS document declares, in its front matter::

    ---
    type: requirements
    title: Data logger requirements
    description: What the data logger must do to record flight data.
    ---

``CommonParser`` reads them into a ``Metadata``; ``CommonValidator`` checks it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metadata:
    """The front matter keys shared by every document.

    A key is ``None`` when it is missing or unusable; the parser has then
    already reported why.
    """

    doc_type: str | None
    """The document's type, always one of the registered types when set."""
    title: str | None
    description: str | None
