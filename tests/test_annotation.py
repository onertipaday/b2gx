from b2gx.model import CandidateGO
from b2gx.config import AnnotationParams
from b2gx.stages.annotation import annotate_sequence


def test_single_strong_term_passes(toy_dag):
    # ppos 90, IEA(0.7): DT=0.63, AS=63 >= 55 -> assigned, most specific kept.
    cands = [CandidateGO("GO:CHILD", "IEA", "WP_s.1", 90.0)]
    params = AnnotationParams()
    out = annotate_sequence(cands, toy_dag, params)
    ids = {a.go_id for a in out}
    assert ids == {"GO:CHILD"}
    assert out[0].score >= 55


def test_weak_term_rescued_by_corroborating_children(toy_dag):
    # Two children at ppos 60, IEA(0.7): each DT=0.42, AS_child=42 (<55).
    # MID gets propagatedDT=0.42 -> 42, plus go_weight*2 = 10 -> 52 (<55 default).
    # Lower cutoff to 50 to assert MID is selected as the abstraction.
    cands = [
        CandidateGO("GO:CHILD", "IEA", "WP_a.1", 60.0),
        CandidateGO("GO:CHILD2", "IEA", "WP_b.1", 60.0),
    ]
    params = AnnotationParams(annotation_cutoff=50)
    out = annotate_sequence(cands, toy_dag, params)
    ids = {a.go_id for a in out}
    assert "GO:MID" in ids
    assert "GO:CHILD" not in ids  # children below cutoff, abstracted to MID


def test_nothing_passes_returns_empty(toy_dag):
    cands = [CandidateGO("GO:CHILD", "ND", "WP_a.1", 90.0)]  # ECW ND=0 -> DT=0
    out = annotate_sequence(cands, toy_dag, AnnotationParams())
    assert out == []
