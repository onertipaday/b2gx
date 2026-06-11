from __future__ import annotations
from pathlib import Path
import polars as pl

# 1-based idmapping_selected columns -> 0-based indices we read
_COL_AC = 0
_COL_REFSEQ = 3
_COL_GO = 6


def build_accession_index(idmapping_gz: str | Path, out_parquet: str | Path) -> None:
    """Stream idmapping_selected.tab.gz -> exploded (refseq, go_id) Parquet keyed on RefSeq."""
    lf = pl.scan_csv(
        idmapping_gz, separator="\t", has_header=False, infer_schema_length=0,
        truncate_ragged_lines=True,
    )
    refseq_col = f"column_{_COL_REFSEQ + 1}"
    go_col = f"column_{_COL_GO + 1}"
    out = (
        lf.select(
            pl.col(refseq_col).alias("refseq_raw"),
            pl.col(go_col).alias("go_raw"),
        )
        .filter(pl.col("refseq_raw").is_not_null() & (pl.col("refseq_raw") != ""))
        .filter(pl.col("go_raw").is_not_null() & (pl.col("go_raw") != ""))
        .with_columns(
            pl.col("refseq_raw").str.replace_all(" ", "").str.split(";").alias("refseq"),
            pl.col("go_raw").str.replace_all(" ", "").str.split(";").alias("go_id"),
        )
        .explode("refseq")
        .explode("go_id")
        .filter((pl.col("refseq") != "") & (pl.col("go_id") != ""))
        .select("refseq", "go_id")
        .unique()
    )
    out.sink_parquet(out_parquet)


def query_go(index_parquet: str | Path, refseq_accs: list[str]) -> pl.DataFrame:
    """Return (refseq, go_id) rows for the requested accessions via an indexed join."""
    keys = pl.DataFrame({"refseq": list(dict.fromkeys(refseq_accs))})
    return (
        pl.scan_parquet(index_parquet)
        .join(keys.lazy(), on="refseq", how="inner")
        .collect()
    )
