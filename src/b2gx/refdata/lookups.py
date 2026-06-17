from __future__ import annotations
from pathlib import Path
import polars as pl

# 1-based idmapping_selected columns -> 0-based indices we read
_COL_REFSEQ = 3
_COL_GO = 6
_COL_EMBL_CDS = 17

# 0-based gene2accession.gz columns we read (NCBI gene/DATA format)
_G2A_COL_GENE_ID = 1
_G2A_COL_PROTEIN_ACC = 5

# 0-based gene2go.gz columns we read (NCBI gene/DATA format)
_G2G_COL_GENE_ID = 1
_G2G_COL_GO_ID = 2


def _explode_key_go(lf: pl.LazyFrame, key_col_0based: int, go_col_0based: int) -> pl.LazyFrame:
    """Select (key, go) from idmapping columns, split ';'-lists, explode to long form."""
    key_col = f"column_{key_col_0based + 1}"
    go_col = f"column_{go_col_0based + 1}"
    return (
        lf.select(
            pl.col(key_col).alias("acc_raw"),
            pl.col(go_col).alias("go_raw"),
        )
        .filter(pl.col("acc_raw").is_not_null() & (pl.col("acc_raw") != ""))
        .filter(pl.col("go_raw").is_not_null() & (pl.col("go_raw") != ""))
        .with_columns(
            pl.col("acc_raw").str.replace_all(" ", "").str.split(";").alias("acc"),
            pl.col("go_raw").str.replace_all(" ", "").str.split(";").alias("go_id"),
        )
        .explode("acc")
        .explode("go_id")
        .filter((pl.col("acc") != "") & (pl.col("go_id") != ""))
        .select("acc", "go_id")
    )


def build_accession_index(idmapping_gz: str | Path, out_parquet: str | Path) -> None:
    """Stream idmapping_selected.tab.gz -> exploded (acc, go_id) Parquet.

    Keys on both the RefSeq column and the EMBL-CDS (GenBank-style protein
    accession) column, since DIAMOND-vs-nr subjects show up under either
    accession family.
    """
    lf = pl.scan_csv(
        idmapping_gz, separator="\t", has_header=False, infer_schema_length=0,
        truncate_ragged_lines=True,
    )
    refseq = _explode_key_go(lf, _COL_REFSEQ, _COL_GO)
    embl_cds = _explode_key_go(lf, _COL_EMBL_CDS, _COL_GO)
    pl.concat([refseq, embl_cds]).unique().sink_parquet(out_parquet)


def build_gene2go_index(
    gene2accession_gz: str | Path, gene2go_gz: str | Path, out_parquet: str | Path
) -> None:
    """Stream gene2accession.gz + gene2go.gz -> (acc, go_id) Parquet via GeneID join.

    Both NCBI files start with a '#'-prefixed format header, which scan_csv
    skips via comment_prefix. NCBI uses '-' as a null placeholder.
    """
    gene_col = f"column_{_G2A_COL_GENE_ID + 1}"
    prot_col = f"column_{_G2A_COL_PROTEIN_ACC + 1}"
    acc_lf = (
        pl.scan_csv(
            gene2accession_gz, separator="\t", has_header=False, infer_schema_length=0,
            comment_prefix="#",
        )
        .select(pl.col(gene_col).alias("gene_id"), pl.col(prot_col).alias("acc"))
        .filter((pl.col("gene_id") != "-") & (pl.col("acc") != "-") & (pl.col("acc") != ""))
    )

    go_gene_col = f"column_{_G2G_COL_GENE_ID + 1}"
    go_id_col = f"column_{_G2G_COL_GO_ID + 1}"
    go_lf = (
        pl.scan_csv(
            gene2go_gz, separator="\t", has_header=False, infer_schema_length=0,
            comment_prefix="#",
        )
        .select(pl.col(go_gene_col).alias("gene_id"), pl.col(go_id_col).alias("go_id"))
        .filter((pl.col("gene_id") != "-") & (pl.col("go_id") != "-") & (pl.col("go_id") != ""))
    )

    (
        acc_lf.join(go_lf, on="gene_id", how="inner")
        .select("acc", "go_id")
        .unique()
        .sink_parquet(out_parquet)
    )


def merge_acc2go_indexes(in_parquets: list[str | Path], out_parquet: str | Path) -> None:
    """Union multiple (acc, go_id) Parquet indexes into one deduped Parquet."""
    pl.concat([pl.scan_parquet(p) for p in in_parquets]).unique().sink_parquet(out_parquet)


def query_go(index_parquet: str | Path, accs: list[str]) -> pl.DataFrame:
    """Return (acc, go_id) rows for the requested accessions via an indexed join."""
    keys = pl.DataFrame({"acc": list(dict.fromkeys(accs))})
    return (
        pl.scan_parquet(index_parquet)
        .join(keys.lazy(), on="acc", how="inner")
        .collect()
    )
