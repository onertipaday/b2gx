from b2gx.model import GOAssignment
from b2gx.stages.interpro import parse_interpro_go, merge_interpro


def test_parse_interpro_go(tmp_path):
    p = tmp_path / "ipr.tsv"
    # 13 cols; col1 query, col12 GO field
    p.write_text(
        "Q1\tmd5\t300\tPfam\tPF1\tdesc\t1\t300\t1e-30\tT\tdate\tGO:0008150|GO:0003674\tIPR1\n"
        "Q1\tmd5\t300\tPfam\tPF2\tdesc\t1\t300\t1e-10\tT\tdate\t-\tIPR2\n"
        "Q2\tmd5\t100\tPfam\tPF3\tdesc\t1\t100\t1e-5\tT\tdate\tGO:0005575\tIPR3\n"
    )
    by_seq = parse_interpro_go(p)
    assert by_seq["Q1"] == {"GO:0008150", "GO:0003674"}
    assert by_seq["Q2"] == {"GO:0005575"}


def test_merge_interpro_dedups():
    existing = [GOAssignment("GO:0008150", "blast", "IEA", 60.0)]
    merged = merge_interpro(existing, {"GO:0008150", "GO:0009999"})
    ids = {(a.go_id, a.source) for a in merged}
    assert ("GO:0008150", "blast") in ids
    assert ("GO:0009999", "interpro") in ids
    assert len(merged) == 2  # GO:0008150 not duplicated
