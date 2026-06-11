import gzip
import polars as pl
from b2gx.refdata.lookups import build_accession_index, query_go


def _fake_idmapping(tmp_path):
    # columns: AC, ID, GeneID, RefSeq, GI, PDB, GO, ... (we only need 1,4,7)
    rows = [
        ["P001", "X_Y", "1", "WP_s.1;WP_z.1", "", "", "GO:0008150; GO:0003674"],
        ["P002", "A_B", "2", "WP_t.1", "", "", "GO:0005575"],
        ["P003", "C_D", "3", "", "", "", "GO:0009999"],  # no RefSeq -> skipped
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
    assert set(df.columns) >= {"refseq", "go_id"}
    go = query_go(out, ["WP_s.1", "WP_t.1", "WP_absent.1"])
    assert set(go.filter(pl.col("refseq") == "WP_s.1")["go_id"]) == {"GO:0008150", "GO:0003674"}
    assert set(go.filter(pl.col("refseq") == "WP_t.1")["go_id"]) == {"GO:0005575"}
    assert go.filter(pl.col("refseq") == "WP_absent.1").height == 0
