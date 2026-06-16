from b2gx.stages.eckegg import parse_ec2go, assign_ec, assign_kegg


def test_parse_ec2go(tmp_path):
    # Real GO external2go/ec2go layout: EC on the left, GO name+id on the right.
    # The right-hand side's GO *name* is itself prefixed "GO:", so only the
    # 7-digit GO id (after ";") is the actual term.
    p = tmp_path / "ec2go"
    p.write_text(
        "! comment line\n"
        "EC:6.2.1.3 > GO:long-chain fatty acid-CoA ligase activity ; GO:0004321\n"
        "EC:1.-.-.- > GO:oxidoreductase activity ; GO:0016491\n"
    )
    m = parse_ec2go(p)
    assert m["GO:0004321"] == {"6.2.1.3"}
    assert m["GO:0016491"] == {"1.-.-.-"}


def test_assign_ec_from_assigned_gos():
    ec2go = {"GO:0004321": {"6.2.1.3"}, "GO:0003824": {"1"}}
    assert assign_ec(["GO:0004321", "GO:0009999"], ec2go) == ["6.2.1.3"]


def test_assign_kegg_from_subjects():
    acc2ko = {"WP_s.1": "K00001", "WP_t.1": "K00002"}
    ko2path = {"K00001": ["map00010"], "K00002": ["map00020"]}
    ko, paths = assign_kegg(["WP_s.1", "WP_t.1", "WP_x.1"], acc2ko, ko2path)
    assert ko == ["K00001", "K00002"]
    assert paths == ["map00010", "map00020"]
