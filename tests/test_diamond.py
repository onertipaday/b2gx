import polars as pl
import pytest
from b2gx.io.diamond import COLUMNS, read_diamond


def _write(tmp_path, rows):
    p = tmp_path / "hits.tsv"
    p.write_text("\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    return p


def test_read_diamond_parses_columns(tmp_path):
    p = _write(tmp_path, [
        ["WP_q.1", "WP_s.1", 70.0, 82.5, 300, 1e-40, 250.0, 95.0],
        ["WP_q.1", "WP_t.1", 60.0, 75.0, 280, 1e-20, 180.0, 90.0],
    ])
    df = read_diamond(p)
    assert df.columns == COLUMNS
    assert df.height == 2
    assert df["ppos"].to_list() == [82.5, 75.0]
    assert df["qcovhsp"].to_list() == [95.0, 90.0]


def test_read_diamond_rejects_wrong_column_count(tmp_path):
    p = _write(tmp_path, [["WP_q.1", "WP_s.1", 70.0]])
    with pytest.raises(ValueError, match="expected 8 columns"):
        read_diamond(p)
