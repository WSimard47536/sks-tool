"""The ``Validator`` interface, and the root validator shared by every document.

A validator checks a structure that was read successfully and returns the
rules it breaks; an empty list means the structure is valid.

``CommonValidator`` runs the checks shared by every document type, on its
front matter metadata.
"""

from typing import Protocol

from sks_tool.docs.base import Metadata
from sks_tool.findings import ValidatorFinding

TITLE_MAX_WORDS = 5
DESCRIPTION_MAX_WORDS = 100


class Validator[T](Protocol):
    """Checks a structure of type ``T``."""

    def validate(self, target: T, /) -> list[ValidatorFinding]:
        """Return the rules ``target`` breaks."""
        ...


class CommonValidator:
    """Runs the checks shared by every document type."""

    def validate(self, metadata: Metadata) -> list[ValidatorFinding]:
        """Return the shared rules the document's metadata breaks.

        A key that is ``None`` was missing or unusable and has already been
        reported by the parser, so it is not checked again.
        """
        findings: list[ValidatorFinding] = []
        if metadata.title is not None:
            findings += _check_words("title", metadata.title, TITLE_MAX_WORDS, "shorten the title")
        if metadata.description is not None:
            findings += _check_words(
                "description",
                metadata.description,
                DESCRIPTION_MAX_WORDS,
                "shorten the description; details belong in the document itself",
            )
        return findings


def _check_words(key: str, text: str, max_words: int, shorten_hint: str) -> list[ValidatorFinding]:
    # Words are runs of characters separated by whitespace.
    words = len(text.split())
    location = ("front matter", key)
    if words == 0:
        return [
            ValidatorFinding(
                code=f"{key}-empty",
                message="is empty",
                hint=f"write the document's {key}",
                location=location,
            )
        ]
    if words > max_words:
        return [
            ValidatorFinding(
                code=f"{key}-too-long",
                message=f"has {words} words; the limit is {max_words}",
                hint=shorten_hint,
                location=location,
            )
        ]
    return []
