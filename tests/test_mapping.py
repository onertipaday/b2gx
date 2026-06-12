import polars as pl
from b2gx.config import AnnotationParams
from b2gx.stages.mapping import map_candidates


def test_map_candidates_and_coverage(tmp_path):
    hits = pl.DataFrame({
        "qseqid": ["Q1", "Q1", "Q2"],
        "sseqid": ["WP_s.1", "WP_z.1", "WP_absent.1"],
        "pident": [70.0, 60.0, 90.0],
        "ppos": [82.0, 75.0, 95.0],
        "length": [300, 280, 100],
        "evalue": [1e-40, 1e-20, 1e-50],
        "bitscore": [250.0, 180.0, 200.0],
        "qcovhsp": [95.0, 90.0, 99.0],
    })
    idx = tmp_path / "acc2go.parquet"
    pl.DataFrame({
        "refseq": ["WP_s.1", "WP_s.1", "WP_z.1"],
        "go_id": ["GO:0008150", "GO:0003674", "GO:0005575"],
    }).write_parquet(idx)

    cand_by_seq, coverage = map_candidates(hits, idx, AnnotationParams())
    q1 = {c.go_id for c in cand_by_seq["Q1"]}
    assert q1 == {"GO:0008150", "GO:0003674", "GO:0005575"}
    assert "Q2" not in cand_by_seq  # WP_absent.1 had no GO
    assert round(coverage.resolved_fraction, 3) == round(2 / 3, 3)


def test_evalue_filter_drops_weak_hits(tmp_path):
    hits = pl.DataFrame({
        "qseqid": ["Q1"], "sseqid": ["WP_s.1"], "pident": [40.0], "ppos": [50.0],
        "length": [100], "evalue": [1e-3], "bitscore": [40.0], "qcovhsp": [80.0],
    })
    idx = tmp_path / "i.parquet"
    pl.DataFrame({"refseq": ["WP_s.1"], "go_id": ["GO:0008150"]}).write_parquet(idx)
    cand_by_seq, _ = map_candidates(hits, idx, AnnotationParams())  # cutoff 1e-6
    assert cand_by_seq == {}
