from __future__ import annotations
from pathlib import Path
import typer
from b2gx.refdata.godag import GODag
from benchmark.concordance import build_report

app = typer.Typer()


@app.command()
def main(annot: Path, emapper: Path, obo: Path, out: Path) -> None:
    dag = GODag.from_obo(obo)
    df = build_report(annot, emapper, dag, out)
    mean_j = df["go_jaccard"].mean() if df.height else 0.0
    typer.echo(f"sequences compared: {df.height}")
    typer.echo(f"mean ancestor-aware GO Jaccard: {mean_j:.3f}")
    typer.echo(f"report: {out}")


if __name__ == "__main__":
    app()
