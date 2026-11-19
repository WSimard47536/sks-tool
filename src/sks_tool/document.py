"""Reading an SKS document from disk: the front matter header and the Markdown body.

An SKS document is a Markdown file that starts with a YAML front matter block::

    ---
    type: requirements
    title: Data logger requirements
    description: What the data logger must do to record flight data.
    ---

    (Markdown body)

This module only splits a file into those two parts. Reading the body into
its structure is the job of ``sks_tool.parsers``; checking that structure is
the job of ``sks_tool.validators``.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

from sks_tool.findings import ParserFinding

FRONT_MATTER_DELIMITER = "---"


@dataclass(frozen=True)
class Document:
    """A document split into its front matter and its body."""

    path: Path
    front_matter: dict[str, object]
    body: str
    body_line: int
    """1-based line number of the first line of ``body`` in the file."""


def load_document(path: Path) -> tuple[Document | None, list[ParserFinding]]:
    """Read ``path`` and split it into front matter and body.

    Returns the document, or ``None`` plus the findings that prevented it from
    being read.
    """
    if not path.is_file():
        return None, [
            ParserFinding(
                code="file-not-found",
                message="file does not exist",
                hint="check the path in sks.toml; it is relative to the folder holding sks.toml",
            )
        ]
    try:
        # utf-8-sig tolerates the byte-order mark some Windows editors add;
        # read_text() normalises CRLF line endings to "\n".
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return None, [
            ParserFinding(
                code="file-not-utf8",
                message="file is not valid UTF-8 text",
                hint="save the file with UTF-8 encoding",
            )
        ]

    lines = text.split("\n")
    if lines[0].rstrip() != FRONT_MATTER_DELIMITER:
        return None, [
            ParserFinding(
                code="front-matter-missing",
                message="the file does not start with a front matter block",
                hint=f"make the first line '{FRONT_MATTER_DELIMITER}', then 'type: <type>', "
                f"then a closing '{FRONT_MATTER_DELIMITER}'",
                line=1,
            )
        ]

    closing_index = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.rstrip() == FRONT_MATTER_DELIMITER),
        None,
    )
    if closing_index is None:
        return None, [
            ParserFinding(
                code="front-matter-unterminated",
                message="the front matter block is never closed",
                hint=f"add a '{FRONT_MATTER_DELIMITER}' line after the last front matter entry",
                line=1,
            )
        ]

    try:
        data = yaml.safe_load("\n".join(lines[1:closing_index]))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        # The YAML text starts on line 2 of the file and marks are 0-based.
        line = mark.line + 2 if mark is not None else 2
        problem = getattr(exc, "problem", None) or "could not be parsed"
        return None, [
            ParserFinding(
                code="front-matter-invalid-yaml",
                message=f"front matter is not valid YAML: {problem}",
                hint="fix the YAML syntax on this line; if a value contains ': ', put the value in quotes",
                line=line,
            )
        ]

    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, [
            ParserFinding(
                code="front-matter-not-mapping",
                message="front matter is not a set of 'key: value' pairs",
                hint="write each entry as 'key: value', e.g. 'type: requirements'",
                line=2,
            )
        ]

    # closing_index is 0-based, so the closing delimiter is file line
    # closing_index + 1 and the body starts on the line after it.
    body_line = closing_index + 2
    document = Document(
        path=path,
        front_matter={str(key): value for key, value in data.items()},
        body="\n".join(lines[closing_index + 1 :]),
        body_line=body_line,
    )
    return document, []
