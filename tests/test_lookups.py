import gzip
import polars as pl
from b2gx.refdata.lookups import (
    build_accession_index,
    build_gene2go_index,
    merge_acc2go_indexes,
    query_go,
)

# idmapping_selected.tab.gz has 22 tab-separated columns; we only populate the
# ones build_accession_index reads: AC(0), RefSeq(3), GO(6), EMBL-CDS(17).
_N_COLS = 22


def _idmapping_row(ac, refseq="", go="", embl_cds=""):
    row = [""] * _N_COLS
    row[0] = ac
    row[3] = refseq
    row[6] = go
    row[17] = embl_cds
    return row


def _fake_idmapping(tmp_path):
    rows = [
        _idmapping_row("P001", refseq="WP_s.1;WP_z.1", go="GO:0008150; GO:0003674"),
        _idmapping_row("P002", refseq="WP_t.1", go="GO:0005575"),
        _idmapping_row("P003", go="GO:0009999"),  # no RefSeq/EMBL-CDS -> skipped
        _idmapping_row("P004", go="GO:0001234", embl_cds="AAT41948.1"),
    ]
    p = tmp_path / "idmapping_selected.tab.gz"
    with gzip.open(p, "wt") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    return p


def test_build_and_query(tmp_path):
    src = _fake_idmapping(tmp_path)
    out = tmp_path / "acc2go.parquet"
    build_accession_index(src, out)
    df = pl.read_parquet(out)
    assert set(df.columns) >= {"acc", "go_id"}
    go = query_go(out, ["WP_s.1", "WP_t.1", "WP_absent.1"])
    assert set(go.filter(pl.col("acc") == "WP_s.1")["go_id"]) == {"GO:0008150", "GO:0003674"}
    assert set(go.filter(pl.col("acc") == "WP_t.1")["go_id"]) == {"GO:0005575"}
    assert go.filter(pl.col("acc") == "WP_absent.1").height == 0


def test_build_and_query_embl_cds(tmp_path):
    """EMBL-CDS column (GenBank-style accessions) must resolve too."""
    src = _fake_idmapping(tmp_path)
    out = tmp_path / "acc2go.parquet"
    build_accession_index(src, out)
    go = query_go(out, ["AAT41948.1"])
    assert set(go["go_id"]) == {"GO:0001234"}


def _fake_gene2accession(tmp_path):
    rows = [
        ["#tax_id", "GeneID", "status", "RNA_nucleotide_accession.version",
         "RNA_nucleotide_gi", "protein_accession.version"],  # header, skipped
        ["1", "100", "PROVISIONAL", "-", "-", "WP_100.1"],
        ["1", "200", "PROVISIONAL", "-", "-", "WP_200.1"],
        ["1", "300", "PROVISIONAL", "-", "-", "-"],  # no protein -> skipped
    ]
    p = tmp_path / "gene2accession.gz"
    with gzip.open(p, "wt") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    return p


def _fake_gene2go(tmp_path):
    rows = [
        ["#tax_id", "GeneID", "GO_ID", "Evidence", "Qualifier", "GO_term",
         "PubMed", "Category"],  # header, skipped
        ["1", "100", "GO:0006412", "IEA", "-", "translation", "-", "Process"],
        ["1", "100", "GO:0003735", "IEA", "-", "structural", "-", "Function"],
        ["1", "400", "GO:0009999", "IEA", "-", "x", "-", "Process"],  # no matching gene2accession row
    ]
    p = tmp_path / "gene2go.gz"
    with gzip.open(p, "wt") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")
    return p


def test_build_gene2go_index(tmp_path):
    g2a = _fake_gene2accession(tmp_path)
    g2g = _fake_gene2go(tmp_path)
    out = tmp_path / "acc2go_gene2go.parquet"
    build_gene2go_index(g2a, g2g, out)
    df = pl.read_parquet(out)
    assert set(df.columns) >= {"acc", "go_id"}

    rows_100 = set(df.filter(pl.col("acc") == "WP_100.1")["go_id"])
    assert rows_100 == {"GO:0006412", "GO:0003735"}

    # GeneID 200 has a protein but no gene2go rows -> absent
    assert df.filter(pl.col("acc") == "WP_200.1").height == 0
    # GeneID 300's protein was "-" -> filtered out entirely, never appears
    assert df.filter(pl.col("acc") == "-").height == 0
    # GeneID 400 has GO but no gene2accession row -> not joined, no orphan acc
    assert "GO:0009999" not in set(df["go_id"])


def test_merge_acc2go_indexes(tmp_path):
    a = tmp_path / "a.parquet"
    b = tmp_path / "b.parquet"
    out = tmp_path / "merged.parquet"
    pl.DataFrame({
        "acc": ["X1", "X2"],
        "go_id": ["GO:0000001", "GO:0000002"],
    }).write_parquet(a)
    pl.DataFrame({
        "acc": ["X2", "X3"],  # X2/GO:0000002 overlaps with `a`
        "go_id": ["GO:0000002", "GO:0000003"],
    }).write_parquet(b)

    merge_acc2go_indexes([a, b], out)
    df = pl.read_parquet(out)
    assert df.height == 3  # deduped union
    assert set(zip(df["acc"], df["go_id"])) == {
        ("X1", "GO:0000001"), ("X2", "GO:0000002"), ("X3", "GO:0000003"),
    }
