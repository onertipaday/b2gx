from b2gx.stages.eckegg import parse_ec2go, assign_ec, assign_kegg


def test_parse_ec2go(tmp_path):
    p = tmp_path / "ec2go"
    p.write_text(
        "! comment line\n"
        "GO:0004321 glutamate... > EC:6.2.1.3 ; EC 6.2.1.3\n"
        "GO:0003824 catalytic activity > EC:1 ; EC 1\n"
    )
    m = parse_ec2go(p)
    assert m["GO:0004321"] == {"6.2.1.3"}
    assert m["GO:0003824"] == {"1"}


def test_assign_ec_from_assigned_gos():
    ec2go = {"GO:0004321": {"6.2.1.3"}, "GO:0003824": {"1"}}
    assert assign_ec(["GO:0004321", "GO:0009999"], ec2go) == ["6.2.1.3"]


def test_assign_kegg_from_subjects():
    acc2ko = {"WP_s.1": "K00001", "WP_t.1": "K00002"}
    ko2path = {"K00001": ["map00010"], "K00002": ["map00020"]}
    ko, paths = assign_kegg(["WP_s.1", "WP_t.1", "WP_x.1"], acc2ko, ko2path)
    assert ko == ["K00001", "K00002"]
    assert paths == ["map00010", "map00020"]
