import polars as pl
from b2gx.config import AnnotationParams
from b2gx.pipeline import run_pipeline


def test_run_pipeline_end_to_end(tmp_path, toy_dag):
    hits = pl.DataFrame({
        "qseqid": ["Q1", "Q1"],
        "sseqid": ["WP_s.1", "WP_z.1"],
        "pident": [88.0, 85.0], "ppos": [92.0, 90.0],
        "length": [300, 280], "evalue": [1e-40, 1e-30],
        "bitscore": [250.0, 240.0], "qcovhsp": [95.0, 92.0],
    })
    idx = tmp_path / "acc2go.parquet"
    pl.DataFrame({
        "refseq": ["WP_s.1", "WP_z.1"],
        "go_id": ["GO:CHILD", "GO:CHILD2"],
    }).write_parquet(idx)

    anns, coverage = run_pipeline(
        hits=hits, index_parquet=idx, dag=toy_dag, params=AnnotationParams(annotation_cutoff=50),
        ec2go={"GO:MID": {"1.1.1.1"}}, acc2ko={"WP_s.1": "K00001"},
        ko2path={"K00001": ["map00010"]},
    )
    assert len(anns) == 1
    a = anns[0]
    assert a.seq_id == "Q1"
    assigned = {g.go_id for g in a.assigned_gos}
    assert assigned == {"GO:CHILD", "GO:CHILD2"}
    assert a.kegg_ko == ["K00001"]
    assert coverage.resolved_fraction == 1.0
