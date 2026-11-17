import json
from pathlib import Path
from typing import Annotated

import typer

from sks_tool import __version__
from sks_tool.doctypes import DOC_TYPES
from sks_tool.manifest import MANIFEST_NAME, ManifestError, load_manifest
from sks_tool.parsers.common import Result, validate_file

EXIT_INVALID = 1
"""Exit code when at least one document fails validation."""
EXIT_USAGE = 2
"""Exit code when the tool was called wrongly or the document list is unusable."""

app = typer.Typer(
    name="sks-tool",
    help="Templates and validators for Structured Knowledge Standard (SKS) documents.",
    no_args_is_help=True,
)


@app.command()
def new(
    doc_type: Annotated[str, typer.Argument(metavar="TYPE", help="Document type; see `sks-tool types`.")],
    path: Annotated[Path, typer.Argument(help="Where to create the document.")],
) -> None:
    """Create a new document from the template for TYPE."""
    if doc_type not in DOC_TYPES:
        typer.echo(f"Unknown document type '{doc_type}'. Expected one of: {', '.join(DOC_TYPES)}.", err=True)
        raise typer.Exit(EXIT_USAGE)
    if path.exists():
        typer.echo(f"{path} already exists; it was not overwritten.", err=True)
        raise typer.Exit(EXIT_USAGE)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DOC_TYPES[doc_type].template(), encoding="utf-8", newline="\n")
    typer.echo(f"Created {path} ({doc_type}). Add it to {MANIFEST_NAME} to have it validated.")


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Option("--config", help="The list of documents to validate."),
    ] = Path(MANIFEST_NAME),
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print the results as JSON instead of text."),
    ] = False,
) -> None:
    """Validate every document in the list.

    Exits with 0 if every document is valid, 1 if any document has an issue,
    and 2 if the list itself is missing or malformed.
    """
    try:
        document_paths = load_manifest(config)
    except ManifestError as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc), "documents": []}, indent=2))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_USAGE) from exc

    # Paths in the list are relative to the folder holding the list.
    results = {path: validate_file(config.parent / path) for path in document_paths}
    all_ok = all(result.ok for result in results.values())

    if json_output:
        typer.echo(json.dumps(_as_json(results), indent=2))
    else:
        _print_text(results)
    if not all_ok:
        raise typer.Exit(EXIT_INVALID)


def _as_json(results: dict[str, Result]) -> dict[str, object]:
    return {
        "ok": all(result.ok for result in results.values()),
        "error": None,
        "documents": [
            {
                "path": path,
                "type": result.doc_type,
                "ok": result.ok,
                "issues": [{"line": issue.line, "code": issue.code, "message": issue.message} for issue in result.issues],
            }
            for path, result in results.items()
        ],
    }


def _print_text(results: dict[str, Result]) -> None:
    for path, result in results.items():
        if result.ok:
            typer.echo(f"{path}: ok ({result.doc_type})")
        for issue in result.issues:
            location = path if issue.line is None else f"{path}:{issue.line}"
            typer.echo(f"{location}: {issue.message} [{issue.code}]")

    failed = sum(not result.ok for result in results.values())
    issues = sum(len(result.issues) for result in results.values())
    summary = f"{len(results)} document(s) checked: {len(results) - failed} ok, {failed} failed"
    if issues:
        summary += f" ({issues} issue(s))"
    typer.echo(f"\n{summary}")


@app.command()
def types() -> None:
    """List the known document types."""
    width = max(len(name) for name in DOC_TYPES)
    for doc_type in DOC_TYPES.values():
        typer.echo(f"{doc_type.name:<{width}}  {doc_type.summary}")


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
