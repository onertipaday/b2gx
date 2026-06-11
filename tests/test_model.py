from b2gx.model import Hit, CandidateGO, GOAssignment, SequenceAnnotation


def test_sequence_annotation_construction():
    h = Hit(sseqid="WP_1.1", ppos=80.0, evalue=1e-30, bitscore=200.0, hsp_cov=0.9)
    c = CandidateGO(go_id="GO:0008150", evidence="IEA", sseqid="WP_1.1", similarity=80.0)
    a = GOAssignment(go_id="GO:0008150", source="blast", evidence="IEA", score=56.0)
    sa = SequenceAnnotation(seq_id="WP_q.1", hits=[h], candidate_gos=[c], assigned_gos=[a])
    assert sa.seq_id == "WP_q.1"
    assert sa.hits[0].ppos == 80.0
    assert sa.assigned_gos[0].score == 56.0
    assert sa.interpro == [] and sa.ec == [] and sa.kegg_ko == []
