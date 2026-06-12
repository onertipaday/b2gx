from __future__ import annotations
from pathlib import Path
import polars as pl
from b2gx.refdata.godag import GODag


def ancestor_closure(gos: set[str], dag: GODag) -> set[str]:
    out = set(gos)
    for g in gos:
        out |= dag.ancestors(g)
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def concordance_row(seq_id: str, b2gx_gos: set[str], eggnog_gos: set[str], dag: GODag) -> dict:
    a = ancestor_closure(b2gx_gos, dag)
    b = ancestor_closure(eggnog_gos, dag)
    return {
        "seq_id": seq_id,
        "n_b2gx": len(b2gx_gos),
        "n_eggnog": len(eggnog_gos),
        "go_jaccard": round(jaccard(a, b), 4),
    }


def load_annot_gos(path: str | Path) -> dict[str, set[str]]:
    by_seq: dict[str, set[str]] = {}
    for line in Path(path).read_text().splitlines():
        seq, _, term = line.partition("\t")
        if term.startswith("GO:"):
            by_seq.setdefault(seq, set()).add(term)
    return by_seq


def load_emapper_gos(path: str | Path) -> dict[str, set[str]]:
    by_seq: dict[str, set[str]] = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split("\t")
        seq = cols[0]
        gos = {g for g in cols[9].split(",") if g.startswith("GO:")} if len(cols) > 9 else set()
        if gos:
            by_seq[seq] = gos
    return by_seq


def build_report(annot: str | Path, emapper: str | Path, dag: GODag, out_tsv: str | Path) -> pl.DataFrame:
    b = load_annot_gos(annot)
    e = load_emapper_gos(emapper)
    rows = [
        concordance_row(s, b.get(s, set()), e.get(s, set()), dag)
        for s in sorted(set(b) | set(e))
    ]
    df = pl.DataFrame(rows)
    df.write_csv(out_tsv, separator="\t")
    return df
