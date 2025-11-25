from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .parser import EmptyStatementError, UnsupportedProviderError, parse_many
from .storage import DEFAULT_DB_PATH, insert_transactions, list_transactions

app = typer.Typer(help="Ingesta de PDFs de movimientos bancarios en una tabla única")
console = Console()


def _resolve_paths(paths: list[Path]) -> list[Path]:
    resolved = []
    for path in paths:
        if not path.exists():
            raise typer.BadParameter(f"No se encontró el archivo: {path}")
        resolved.append(path)
    return resolved


@app.command()
def ingest(
    pdf_files: list[Path] = typer.Argument(..., help="Archivos PDF a procesar"),
    db_path: Optional[Path] = typer.Option(None, help="Ruta al archivo SQLite"),
) -> None:
    """Lee los PDFs y guarda los movimientos detectados en SQLite."""

    chosen_db = db_path or DEFAULT_DB_PATH
    pdf_paths = _resolve_paths(pdf_files)

    try:
        transactions = parse_many(pdf_paths)
    except UnsupportedProviderError as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=1) from error
    except EmptyStatementError as error:
        console.print(f"[yellow]Advertencia:[/yellow] {error}")
        raise typer.Exit(code=1) from error

    saved = insert_transactions(transactions, chosen_db)
    console.print(f"Se guardaron [bold]{saved}[/bold] movimientos en {chosen_db}")


@app.command()
def show(db_path: Optional[Path] = typer.Option(None, help="Ruta al archivo SQLite")) -> None:
    """Muestra los movimientos almacenados."""

    chosen_db = db_path or DEFAULT_DB_PATH
    rows = list_transactions(chosen_db)
    if not rows:
        console.print("No hay movimientos cargados todavía")
        raise typer.Exit(code=0)

    table = Table(show_lines=True)
    for column in rows[0].keys():
        table.add_column(column)

    for row in rows:
        table.add_row(*(str(value) if value is not None else "" for value in row.values()))

    console.print(table)


if __name__ == "__main__":
    app()
