import io
import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from sks_tool import __version__
from sks_tool.doctypes import DOC_TYPES
from sks_tool.findings import Finding, ParserFinding, ValidatorFinding
from sks_tool.manifest import MANIFEST_NAME, ManifestError, load_manifest
from sks_tool.pipeline import Result, check_project

EXIT_INVALID = 1
"""Exit code when at least one document has a finding or could not be validated."""
EXIT_USAGE = 2
"""Exit code when the tool was called wrongly or the document list is unusable."""

app = typer.Typer(
    name="sks-tool",
    help="Templates and validators for Structured Knowledge Standard (SKS) documents.",
    no_args_is_help=True,
)


@app.callback()
def _use_utf8_output() -> None:
    # Runs before every command. When the output is redirected (CI logs,
    # "> out.json"), Python writes in the system encoding, which on Windows
    # can be a code page such as cp437 that cannot encode every path or
    # message, and printing would crash. UTF-8 encodes any text; the escape
    # handler only covers undecodable filename bytes.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


@app.command()
def new(
    doc_type: Annotated[str, typer.Argument(metavar="TYPE", help="Document type; see `sks-tool types`.")],
    path: Annotated[Path, typer.Argument(help="Where to create the document.")],
) -> None:
    """Create a new document from the template for TYPE.

    An overview also gets a blank system_diagram.drawio.svg next to it.
    Nothing is written if any of the files already exists.
    """
    if doc_type not in DOC_TYPES:
        typer.echo(f"Unknown document type '{doc_type}'. Expected one of: {', '.join(DOC_TYPES)}.", err=True)
        raise typer.Exit(EXIT_USAGE)
    chosen = DOC_TYPES[doc_type]
    companions = [path.parent / name for name in chosen.companions]
    existing = [target for target in (path, *companions) if target.exists()]
    if existing:
        listed = ", ".join(str(target) for target in existing)
        typer.echo(f"{listed} already exist(s); nothing was written.", err=True)
        raise typer.Exit(EXIT_USAGE)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chosen.template(), encoding="utf-8", newline="\n")
    for name, target in zip(chosen.companions, companions, strict=True):
        target.write_bytes(chosen.companion(name))
    created = " and ".join(str(target) for target in (path, *companions))
    typer.echo(f"Created {created} ({doc_type}). Add {path} to {MANIFEST_NAME} to have it validated.")


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
    """Parse, then validate, every document in the list.

    Each finding says whether it was found while parsing or while validating,
    what is wrong and how to fix it. Exits with 0 if every document is valid,
    1 if any document has a finding, and 2 if the list itself is missing or
    malformed.
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
    results = check_project({path: config.parent / path for path in document_paths})
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
                "validated": result.validated,
                "findings": [_finding_as_json(finding) for finding in result.findings],
            }
            for path, result in results.items()
        ],
    }


def _finding_as_json(finding: Finding) -> dict[str, object]:
    # Every finding has the same keys; those that do not apply to its kind are null.
    line: int | None = None
    location: list[str] | None = None
    match finding:
        case ParserFinding():
            line = finding.line
        case ValidatorFinding():
            line = finding.line
            location = list(finding.location)
    return {
        "kind": finding.kind,
        "code": finding.code,
        "message": finding.message,
        "hint": finding.hint,
        "line": line,
        "location": location,
    }


def _finding_as_text(path: str, finding: Finding) -> str:
    line: int | None = None
    where = ""
    match finding:
        case ParserFinding():
            line = finding.line
        case ValidatorFinding():
            line = finding.line
            if finding.location:
                where = " › ".join(finding.location) + ": "
    position = path if line is None else f"{path}:{line}"
    return f"{position}: {finding.kind}: {where}{finding.message} [{finding.code}]\n    fix: {finding.hint}"


def _print_text(results: dict[str, Result]) -> None:
    for path, result in results.items():
        if result.ok:
            typer.echo(f"{path}: ok ({result.doc_type})")
        for finding in result.findings:
            typer.echo(_finding_as_text(path, finding))
        if not result.validated:
            typer.echo(f"{path}: type-specific validation skipped until the parse findings are fixed")

    all_findings = [finding for result in results.values() for finding in result.findings]
    parse_count = sum(isinstance(finding, ParserFinding) for finding in all_findings)
    validate_count = sum(isinstance(finding, ValidatorFinding) for finding in all_findings)
    skipped = sum(not result.validated for result in results.values())
    failed = sum(not result.ok for result in results.values())

    summary = f"{len(results)} document(s) checked: {len(results) - failed} ok, {failed} failed"
    if failed:
        summary += f" ({parse_count} parse finding(s), {validate_count} validation finding(s), {skipped} skipped)"
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
