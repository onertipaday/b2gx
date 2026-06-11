import polars as pl
from b2gx.model import SequenceAnnotation, GOAssignment
from b2gx.io.writers import write_clusterprofiler, write_annot


def _ann():
    return [
        SequenceAnnotation(
            seq_id="Q1",
            assigned_gos=[GOAssignment("GO:CHILD", "blast", "IEA", 60.0)],
            ec=["6.2.1.3"],
        ),
        SequenceAnnotation(
            seq_id="Q2",
            assigned_gos=[GOAssignment("GO:MID", "interpro", "IEA", None)],
        ),
    ]


def test_write_clusterprofiler(tmp_path, toy_dag):
    write_clusterprofiler(_ann(), toy_dag, tmp_path)
    t2g = pl.read_csv(tmp_path / "go_term2gene.tsv", separator="\t")
    assert set(zip(t2g["go_id"], t2g["seq_id"])) == {("GO:CHILD", "Q1"), ("GO:MID", "Q2")}
    t2n = pl.read_csv(tmp_path / "go_term2name.tsv", separator="\t")
    names = dict(zip(t2n["go_id"], t2n["name"]))
    assert names["GO:MID"] == "metabolic process"


def test_write_annot(tmp_path):
    write_annot(_ann(), tmp_path / "out.annot")
    lines = (tmp_path / "out.annot").read_text().splitlines()
    assert "Q1\tGO:CHILD" in lines
    assert "Q1\tEC:6.2.1.3" in lines
    assert "Q2\tGO:MID" in lines
