import textwrap
from b2gx.config import Config, AnnotationParams


def test_defaults_match_blast2go():
    cfg = Config(query_fasta="q.faa", diamond_tsv="hits.tsv", cache_dir="/cache", out_dir="/out")
    assert cfg.annotation.annotation_cutoff == 55
    assert cfg.annotation.go_weight == 5
    assert cfg.annotation.evalue_hit_filter == 1.0e-6
    assert cfg.annotation.num_hits == 20
    assert cfg.annotation.ecw["IEA"] == 0.7
    assert cfg.annotation.ecw["ND"] == 0.0


def test_yaml_override(tmp_path):
    p = tmp_path / "run.yaml"
    p.write_text(textwrap.dedent("""
        query_fasta: q.faa
        diamond_tsv: hits.tsv
        cache_dir: /cache
        out_dir: /out
        annotation:
          annotation_cutoff: 45
          go_weight: 3
    """))
    cfg = Config.from_yaml(p)
    assert cfg.annotation.annotation_cutoff == 45
    assert cfg.annotation.go_weight == 3
    assert cfg.annotation.num_hits == 20  # untouched default preserved
