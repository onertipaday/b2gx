import networkx as nx
import pytest
from b2gx.refdata.godag import GODag


@pytest.fixture
def toy_dag() -> GODag:
    # Chain: GO:CHILD -is_a-> GO:MID -is_a-> GO:ROOT, plus a sibling child.
    g = nx.DiGraph()  # edge child -> parent
    for n, name, ns in [
        ("GO:ROOT", "biological_process", "biological_process"),
        ("GO:MID", "metabolic process", "biological_process"),
        ("GO:CHILD", "glycolytic process", "biological_process"),
        ("GO:CHILD2", "fermentation", "biological_process"),
    ]:
        g.add_node(n, name=name, namespace=ns)
    g.add_edge("GO:CHILD", "GO:MID", relation="is_a")
    g.add_edge("GO:CHILD2", "GO:MID", relation="is_a")
    g.add_edge("GO:MID", "GO:ROOT", relation="is_a")
    return GODag(graph=g)
