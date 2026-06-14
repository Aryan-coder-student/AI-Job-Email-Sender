from __future__ import annotations

from app.modules.matching.ranker import _merge_project_ids


def test_merge_project_ids_prefers_graph_order_then_vector() -> None:
    merged = _merge_project_ids(
        {"project:a": 0.9, "project:b": 0.2},
        {"project:c": 0.8, "project:a": 0.1},
    )
    assert merged[0] == "project:a"
    assert "project:c" in merged
