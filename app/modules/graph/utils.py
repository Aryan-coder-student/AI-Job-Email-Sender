from __future__ import annotations

from app.modules.graph.model import GraphEdge, GraphNode


def dedupe_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    deduped: dict[str, GraphNode] = {}
    for node in nodes:
        deduped[node.node_id] = node
    return list(deduped.values())


def dedupe_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    deduped: dict[tuple[str, str, str], GraphEdge] = {}
    for edge in edges:
        deduped[(edge.source_id, edge.target_id, edge.relationship)] = edge
    return list(deduped.values())


def persist_graph(
    graph_store,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> tuple[int, int]:
    node_count = graph_store.upsert_nodes(dedupe_nodes(nodes))
    edge_count = graph_store.upsert_edges(dedupe_edges(edges))
    return node_count, edge_count
