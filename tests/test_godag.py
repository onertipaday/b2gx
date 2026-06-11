def test_ancestors_follow_is_a(toy_dag):
    assert toy_dag.ancestors("GO:CHILD") == {"GO:MID", "GO:ROOT"}
    assert toy_dag.ancestors("GO:ROOT") == set()


def test_name_and_namespace(toy_dag):
    assert toy_dag.name("GO:MID") == "metabolic process"
    assert toy_dag.namespace("GO:CHILD") == "biological_process"


def test_children_in_pool(toy_dag):
    pool = {"GO:CHILD", "GO:CHILD2", "GO:ROOT"}
    assert toy_dag.descendants_in("GO:MID", pool) == {"GO:CHILD", "GO:CHILD2"}
