from __future__ import annotations
from pathlib import Path
import polars as pl

COLUMNS = ["qseqid", "sseqid", "pident", "ppos", "length", "evalue", "bitscore", "qcovhsp"]
_DTYPES = [pl.Utf8, pl.Utf8, pl.Float64, pl.Float64, pl.Int64, pl.Float64, pl.Float64, pl.Float64]


def read_diamond(path: str | Path) -> pl.DataFrame:
    """Read DIAMOND outfmt6 with the b2gx-required 8 columns (incl. ppos, qcovhsp)."""
    with Path(path).open() as fh:
        first = fh.readline().rstrip("\n")
    if not first:
        raise ValueError(f"DIAMOND file is empty: {path}")
    if len(first.split("\t")) != len(COLUMNS):
        raise ValueError(
            f"expected 8 columns {COLUMNS}, got {len(first.split(chr(9)))}. "
            "Re-run DIAMOND with: -f 6 qseqid sseqid pident ppos length evalue bitscore qcovhsp"
        )
    return pl.read_csv(
        path, separator="\t", has_header=False,
        new_columns=COLUMNS, schema_overrides=dict(zip(COLUMNS, _DTYPES)),
    )
