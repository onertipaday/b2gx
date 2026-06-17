import gzip
from pathlib import Path
import yaml
from typer.testing import CliRunner
from b2gx.cli import app

runner = CliRunner()

_OBO = """format-version: 1.2

[Term]
id: GO:0008150
name: biological_process
namespace: biological_process

[Term]
id: GO:0009987
name: cellular process
namespace: biological_process
is_a: GO:0008150
"""


def _setup(tmp_path):
    obo = tmp_path / "go-basic.obo"; obo.write_text(_OBO)
    idmap = tmp_path / "idmapping_selected.tab.gz"
    # 22 tab-separated columns; we only populate AC(0), RefSeq(3), GO(6).
    row = ["P1", "ID", "1", "WP_s.1", "", "", "GO:0009987"] + [""] * 15
    with gzip.open(idmap, "wt") as fh:
        fh.write("\t".join(row) + "\n")
    from b2gx.refdata.lookups import build_accession_index
    idx = tmp_path / "acc2go.parquet"; build_accession_index(idmap, idx)
    hits = tmp_path / "hits.tsv"
    hits.write_text("Q1\tWP_s.1\t90.0\t95.0\t300\t1e-40\t250.0\t98.0\n")
    cfg = tmp_path / "run.yaml"
    cfg.write_text(yaml.safe_dump({
        "query_fasta": "unused.faa", "diamond_tsv": str(hits),
        "cache_dir": str(tmp_path), "out_dir": str(tmp_path / "out"),
        "annotation": {"annotation_cutoff": 50},
    }))
    return cfg, obo, idx


def test_run_command_produces_outputs(tmp_path):
    cfg, obo, idx = _setup(tmp_path)
    result = runner.invoke(app, [
        "run", "--config", str(cfg), "--obo", str(obo), "--index", str(idx),
    ])
    assert result.exit_code == 0, result.output
    out = tmp_path / "out"
    assert (out / "go_term2gene.tsv").exists()
    assert (out / "annotation.annot").exists()
    assert (out / "summary.txt").exists()
    assert "GO:0009987" in (out / "annotation.annot").read_text()
