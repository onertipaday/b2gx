from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import networkx as nx
import obonet

_KEEP_RELATIONS = {"is_a", "part_of"}


@dataclass
class GODag:
    graph: nx.DiGraph  # directed child -> parent

    @classmethod
    def from_obo(cls, path: str | Path) -> "GODag":
        raw = obonet.read_obo(str(path))  # nodes carry name/namespace; edges child->parent
        g = nx.DiGraph()
        for node, data in raw.nodes(data=True):
            g.add_node(node, name=data.get("name", node),
                       namespace=data.get("namespace", ""))
        for child, parent, key in raw.edges(keys=True):
            if key in _KEEP_RELATIONS:
                g.add_edge(child, parent, relation=key)
        return cls(graph=g)

    def ancestors(self, go_id: str) -> set[str]:
        if go_id not in self.graph:
            return set()
        return set(nx.descendants(self.graph, go_id))  # child->parent edges: descendants = ancestors

    def descendants_in(self, go_id: str, pool: set[str]) -> set[str]:
        """Members of `pool` that have `go_id` as an ancestor (i.e. more specific terms)."""
        return {p for p in pool if p != go_id and go_id in self.ancestors(p)}

    def name(self, go_id: str) -> str:
        return self.graph.nodes[go_id].get("name", go_id) if go_id in self.graph else go_id

    def namespace(self, go_id: str) -> str:
        return self.graph.nodes[go_id].get("namespace", "") if go_id in self.graph else ""
