"""Concordance between two .annot files (b2gx vs a reference such as Blast2GO).

Both inputs use the Blast2GO .annot layout: ``seq_id<TAB>GO:xxxxxxx`` (one term
per line; EC: lines are ignored). GO sets are propagated to ancestors before
comparison (ancestor-aware Jaccard), identical to the eggNOG benchmark.
"""
from __future__ import annotations
from pathlib import Path
import typer
import polars as pl
from b2gx.refdata.godag import GODag
from benchmark.concordance import load_annot_gos, concordance_row

app = typer.Typer()


@app.command()
def main(b2gx: Path, reference: Path, obo: Path, out: Path) -> None:
    dag = GODag.from_obo(obo)
    a = load_annot_gos(b2gx)        # b2gx output .annot
    r = load_annot_gos(reference)   # reference (Blast2GO) .annot
    rows = [
        concordance_row(s, a.get(s, set()), r.get(s, set()), dag)
        for s in sorted(set(a) | set(r))
    ]
    df = pl.DataFrame(rows)
    df.write_csv(out, separator="\t")

    both = df.filter((pl.col("n_b2gx") > 0) & (pl.col("n_eggnog") > 0))
    typer.echo(f"b2gx proteins with GO:      {df.filter(pl.col('n_b2gx') > 0).height}")
    typer.echo(f"reference proteins with GO: {df.filter(pl.col('n_eggnog') > 0).height}")
    typer.echo(f"proteins where both assign GO: {both.height}")
    if both.height:
        s = both['go_jaccard']
        typer.echo(
            f"overlap mean/median Jaccard: {s.mean():.3f} / {s.median():.3f} "
            f"(p25 {s.quantile(0.25):.3f} / p75 {s.quantile(0.75):.3f})"
        )
    if df.height:
        typer.echo(f"mean Jaccard over all b2gx-annotated: "
                   f"{df.filter(pl.col('n_b2gx') > 0)['go_jaccard'].mean():.3f}")
    typer.echo(f"report: {out}")


if __name__ == "__main__":
    app()
