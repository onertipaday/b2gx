from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer

app = typer.Typer(help="b2gx — Blast2GO-style functional annotation pipeline.")


@app.command()
def version() -> None:
    from b2gx import __version__
    typer.echo(__version__)


@app.command()
def run(
    config: Path = typer.Option(..., "--config", exists=True),
    obo: Path = typer.Option(..., "--obo", exists=True),
    index: Path = typer.Option(..., "--index", exists=True),
    ec2go: Optional[Path] = typer.Option(None, "--ec2go"),
) -> None:
    """Run the full annotation pipeline and write all outputs."""
    from b2gx.config import Config
    from b2gx.io.diamond import read_diamond
    from b2gx.refdata.godag import GODag
    from b2gx.stages.eckegg import parse_ec2go
    from b2gx.pipeline import run_pipeline
    from b2gx.io.writers import (
        write_clusterprofiler, write_annot, write_rich_table, write_summary,
    )

    cfg = Config.from_yaml(config)
    dag = GODag.from_obo(obo)
    hits = read_diamond(cfg.diamond_tsv)
    ec_map = parse_ec2go(ec2go) if ec2go else {}

    anns, coverage = run_pipeline(
        hits=hits, index_parquet=index, dag=dag, params=cfg.annotation, ec2go=ec_map,
    )

    out = Path(cfg.out_dir)
    write_clusterprofiler(anns, dag, out)
    write_annot(anns, out / "annotation.annot")
    write_rich_table(anns, out / "annotation.parquet")
    write_summary(anns, dag, coverage.n_subjects, coverage.n_resolved, out)
    typer.echo(f"Wrote outputs to {out} (coverage={coverage.resolved_fraction:.3f})")


@app.command()
def fetch(
    cache_dir: Path = typer.Option(..., "--cache-dir"),
) -> None:
    """Download reference DBs to the cache and build the accession index."""
    from b2gx.refdata.fetch import SOURCES, download, write_manifest
    from b2gx.refdata.lookups import build_accession_index

    cache_dir.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict] = {}
    for key, url in SOURCES.items():
        dest = cache_dir / Path(url).name
        typer.echo(f"Downloading {key} <- {url}")
        download(url, dest)
        entries[key] = {"path": str(dest), "url": url}
    write_manifest(cache_dir / "manifest.json", entries)
    idmap = Path(entries["idmapping"]["path"])
    build_accession_index(idmap, cache_dir / "acc2go.parquet")
    typer.echo(f"Reference cache ready in {cache_dir}")


if __name__ == "__main__":
    app()
