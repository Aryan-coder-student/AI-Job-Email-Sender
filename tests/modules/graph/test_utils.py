from __future__ import annotations

from app.modules.graph.model import GraphEdge, GraphNode
from app.modules.graph.utils import dedupe_edges, dedupe_nodes


def test_dedupe_nodes_keeps_last_occurrence() -> None:
    first = GraphNode(node_id="project:a", label="Project", name="A")
    second = GraphNode(node_id="project:a", label="Project", name="A updated")
    assert dedupe_nodes([first, second]) == [second]


def test_dedupe_edges_keeps_unique_relationships() -> None:
    edge = GraphEdge(source_id="a", target_id="b", relationship="OWNS")
    assert dedupe_edges([edge, edge]) == [edge]
