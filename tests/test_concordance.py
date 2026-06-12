from benchmark.concordance import ancestor_closure, jaccard, concordance_row


def test_ancestor_closure(toy_dag):
    assert ancestor_closure({"GO:CHILD"}, toy_dag) == {"GO:CHILD", "GO:MID", "GO:ROOT"}


def test_jaccard():
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert jaccard(set(), set()) == 1.0  # both empty = trivially concordant
    assert jaccard({"a"}, set()) == 0.0


def test_concordance_row_is_ancestor_aware(toy_dag):
    # b2gx assigns MID; eggnog assigns CHILD. Raw overlap 0, but ancestor-aware > 0.
    row = concordance_row("Q1", b2gx_gos={"GO:MID"}, eggnog_gos={"GO:CHILD"}, dag=toy_dag)
    assert row["seq_id"] == "Q1"
    assert row["go_jaccard"] > 0.0
