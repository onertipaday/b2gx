from __future__ import annotations
from pathlib import Path
import re

_EC_RE = re.compile(r"EC:([0-9.\-]+)")
_GO_ID_RE = re.compile(r"GO:\d{7}")


def parse_ec2go(path: str | Path) -> dict[str, set[str]]:
    """Build a GO-id -> {EC number} map from a GO external2go ec2go file.

    File layout is ``EC:<number> > GO:<name> ; GO:<id>`` (EC on the left, GO on
    the right). The right side's GO *name* is also "GO:"-prefixed, so the actual
    term is matched as the 7-digit GO id after the ";".
    """
    m: dict[str, set[str]] = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("!") or ">" not in line:
            continue
        left, right = line.split(">", 1)
        ecs = set(_EC_RE.findall(left))
        go_ids = set(_GO_ID_RE.findall(right))
        if not ecs or not go_ids:
            continue
        for go in go_ids:
            m.setdefault(go, set()).update(ecs)
    return m


def assign_ec(assigned_gos: list[str], ec2go: dict[str, set[str]]) -> list[str]:
    out: list[str] = []
    for go in assigned_gos:
        for ec in sorted(ec2go.get(go, set())):
            if ec not in out:
                out.append(ec)
    return out


def assign_kegg(
    subjects: list[str], acc2ko: dict[str, str], ko2path: dict[str, list[str]]
) -> tuple[list[str], list[str]]:
    ko: list[str] = []
    for s in subjects:
        k = acc2ko.get(s)
        if k and k not in ko:
            ko.append(k)
    paths: list[str] = []
    for k in ko:
        for p in ko2path.get(k, []):
            if p not in paths:
                paths.append(p)
    return ko, paths
