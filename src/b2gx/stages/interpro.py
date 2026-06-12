from __future__ import annotations
from pathlib import Path
from b2gx.model import GOAssignment

_GO_COL = 11  # 0-based column index for the GO field in InterProScan TSV


def parse_interpro_go(path: str | Path) -> dict[str, set[str]]:
    by_seq: dict[str, set[str]] = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) <= _GO_COL:
            continue
        field = cols[_GO_COL].strip()
        if not field or field == "-":
            continue
        gos = {g.split("(")[0] for g in field.replace(",", "|").split("|") if g.startswith("GO:")}
        if gos:
            by_seq.setdefault(cols[0], set()).update(gos)
    return by_seq


def merge_interpro(existing: list[GOAssignment], ipr_gos: set[str]) -> list[GOAssignment]:
    present = {a.go_id for a in existing}
    merged = list(existing)
    for go in sorted(ipr_gos):
        if go not in present:
            merged.append(GOAssignment(go_id=go, source="interpro", evidence="IEA", score=None))
    return merged
