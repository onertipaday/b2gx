from __future__ import annotations
from pathlib import Path
import polars as pl
from b2gx.model import SequenceAnnotation
from b2gx.refdata.godag import GODag


def write_clusterprofiler(anns: list[SequenceAnnotation], dag: GODag, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t2g_go = [(a.go_id, s.seq_id) for s in anns for a in s.assigned_gos]
    if t2g_go:
        pl.DataFrame(t2g_go, schema=["go_id", "seq_id"], orient="row").write_csv(
            out / "go_term2gene.tsv", separator="\t"
        )
        go_ids = sorted({go for go, _ in t2g_go})
        pl.DataFrame([(g, dag.name(g)) for g in go_ids], schema=["go_id", "name"], orient="row").write_csv(
            out / "go_term2name.tsv", separator="\t"
        )
    else:
        pl.DataFrame({"go_id": [], "seq_id": []}).write_csv(out / "go_term2gene.tsv", separator="\t")
        pl.DataFrame({"go_id": [], "name": []}).write_csv(out / "go_term2name.tsv", separator="\t")
    t2g_ko = [(ko, s.seq_id) for s in anns for ko in s.kegg_ko]
    if t2g_ko:
        pl.DataFrame(t2g_ko, schema=["ko", "seq_id"], orient="row").write_csv(
            out / "kegg_term2gene.tsv", separator="\t"
        )
    else:
        pl.DataFrame({"ko": [], "seq_id": []}).write_csv(out / "kegg_term2gene.tsv", separator="\t")


def write_annot(anns: list[SequenceAnnotation], path: str | Path) -> None:
    lines: list[str] = []
    for s in anns:
        for a in s.assigned_gos:
            lines.append(f"{s.seq_id}\t{a.go_id}")
        for ec in s.ec:
            lines.append(f"{s.seq_id}\tEC:{ec}")
    Path(path).write_text("\n".join(lines) + ("\n" if lines else ""))


def write_rich_table(anns: list[SequenceAnnotation], path: str | Path) -> None:
    rows = [{
        "seq_id": s.seq_id,
        "go_ids": ";".join(a.go_id for a in s.assigned_gos),
        "go_scores": ";".join(str(a.score) for a in s.assigned_gos),
        "ec": ";".join(s.ec),
        "kegg_ko": ";".join(s.kegg_ko),
        "kegg_pathways": ";".join(s.kegg_pathways),
        "interpro": ";".join(s.interpro),
        "top_hit_desc": s.top_hit_desc or "",
    } for s in anns]
    pl.DataFrame(rows).write_parquet(path)


def slim_map(go_id: str, dag: GODag, slim: set[str]) -> str | None:
    if go_id in slim:
        return go_id
    ancestors = dag.ancestors(go_id)
    candidates = ancestors & slim
    if not candidates:
        return None
    # nearest by shortest path length in the child->parent graph
    import networkx as nx
    best, best_dist = None, None
    for anc in candidates:
        try:
            d = nx.shortest_path_length(dag.graph, go_id, anc)
        except nx.NetworkXNoPath:
            continue
        if best_dist is None or d < best_dist:
            best, best_dist = anc, d
    return best


def write_summary(
    anns: list[SequenceAnnotation], dag: GODag, n_subjects: int, n_resolved: int,
    out_dir: str | Path, slim: set[str] | None = None,
) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    n_annotated = sum(1 for s in anns if s.assigned_gos)
    total_go = sum(len(s.assigned_gos) for s in anns)
    by_ns: dict[str, int] = {}
    for s in anns:
        for a in s.assigned_gos:
            ns = dag.namespace(a.go_id) or "unknown"
            by_ns[ns] = by_ns.get(ns, 0) + 1
    frac = round(n_resolved / n_subjects, 4) if n_subjects else 0.0
    lines = [
        f"sequences_annotated\t{n_annotated}",
        f"total_go_assignments\t{total_go}",
        f"coverage_resolved_fraction\t{frac}",
    ]
    lines += [f"go_by_namespace.{ns}\t{c}" for ns, c in sorted(by_ns.items())]
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    if slim:
        slim_rows = [
            (s.seq_id, slim_map(a.go_id, dag, slim))
            for s in anns for a in s.assigned_gos
            if slim_map(a.go_id, dag, slim)
        ]
        pl.DataFrame(slim_rows, schema=["seq_id", "slim_go"], orient="row").write_csv(
            out / "go_slim.tsv", separator="\t"
        )
