from __future__ import annotations
from b2gx.model import CandidateGO, GOAssignment
from b2gx.config import AnnotationParams
from b2gx.refdata.godag import GODag


def _direct_term_scores(cands: list[CandidateGO], params: AnnotationParams) -> dict[str, float]:
    dt: dict[str, float] = {}
    for c in cands:
        ecw = params.ecw.get(c.evidence, params.ecw.get("IEA", 0.7))
        score = (c.similarity / 100.0) * ecw
        if score > dt.get(c.go_id, 0.0):
            dt[c.go_id] = score
    return dt


def annotate_sequence(
    cands: list[CandidateGO], dag: GODag, params: AnnotationParams
) -> list[GOAssignment]:
    dt = _direct_term_scores(cands, params)
    if not dt:
        return []

    # candidate pool = direct go ids with positive DT; node set = pool ∪ ancestors
    pool = {go for go, s in dt.items() if s > 0.0}
    nodes: set[str] = set(pool)
    for go in pool:
        nodes |= dag.ancestors(go)

    annotation_score: dict[str, float] = {}
    for node in nodes:
        descend = dag.descendants_in(node, pool)
        prop_dt = max([dt.get(node, 0.0)] + [dt[d] for d in descend])
        annotation_score[node] = 100.0 * prop_dt + params.go_weight * len(descend)

    passing = {n for n, a in annotation_score.items() if a >= params.annotation_cutoff}
    if not passing:
        return []

    # keep most specific: drop nodes that are an ancestor of another passing node
    most_specific = {
        n for n in passing
        if not any(other != n and n in dag.ancestors(other) for other in passing)
    }

    return [
        GOAssignment(go_id=n, source="blast", evidence="IEA", score=round(annotation_score[n], 2))
        for n in sorted(most_specific)
    ]
