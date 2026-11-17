"""Reading an SKS document from disk: the front matter header and the Markdown body.

An SKS document is a Markdown file that starts with a YAML front matter block::

    ---
    type: requirements
    ---

    (Markdown body)

This module only splits a file into those two parts. Deciding whether the
content is *valid* is the job of the parsers in ``sks_tool.parsers``.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

FRONT_MATTER_DELIMITER = "---"


@dataclass(frozen=True)
class Issue:
    """One validation problem found in a document."""

    code: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class Document:
    """A document split into its front matter and its body."""

    path: Path
    front_matter: dict[str, object]
    body: str
    body_line: int
    """1-based line number of the first line of ``body`` in the file."""


def load_document(path: Path) -> tuple[Document | None, list[Issue]]:
    """Read ``path`` and split it into front matter and body.

    Returns the document, or ``None`` plus the issues that prevented it from
    being read.
    """
    if not path.is_file():
        return None, [Issue("file-not-found", "file does not exist")]
    try:
        # utf-8-sig tolerates the byte-order mark some Windows editors add;
        # read_text() normalises CRLF line endings to "\n".
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return None, [Issue("file-not-utf8", "file is not valid UTF-8 text")]

    lines = text.split("\n")
    if lines[0].rstrip() != FRONT_MATTER_DELIMITER:
        return None, [
            Issue(
                "front-matter-missing",
                f"the first line must be '{FRONT_MATTER_DELIMITER}' to open the front matter block",
                line=1,
            )
        ]

    closing_index = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.rstrip() == FRONT_MATTER_DELIMITER),
        None,
    )
    if closing_index is None:
        return None, [
            Issue(
                "front-matter-unterminated",
                f"the front matter block is never closed with a '{FRONT_MATTER_DELIMITER}' line",
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
        return None, [Issue("front-matter-invalid-yaml", f"front matter is not valid YAML: {problem}", line=line)]

    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, [
            Issue(
                "front-matter-not-mapping",
                "front matter must be a set of 'key: value' pairs",
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
