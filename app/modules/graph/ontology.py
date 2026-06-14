from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

ONTOLOGY_PATH = Path(__file__).resolve().parent / "data" / "ontology.yaml"


@dataclass(frozen=True)
class Ontology:
    technology_aliases: dict[str, str]
    capability_aliases: dict[str, str]
    technology_categories: dict[str, list[str]]
    capability_categories: dict[str, list[str]]


@lru_cache(maxsize=1)
def load_ontology(path: Path = ONTOLOGY_PATH) -> Ontology:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    technology_categories = raw.get("technology_categories", {})
    capability_categories = raw.get("capability_categories", {})

    technology_aliases = _build_alias_map(technology_categories)
    capability_aliases = _build_alias_map(capability_categories)

    return Ontology(
        technology_aliases=technology_aliases,
        capability_aliases=capability_aliases,
        technology_categories={
            key: list(value.get("aliases", []))
            for key, value in technology_categories.items()
        },
        capability_categories={
            key: list(value.get("aliases", []))
            for key, value in capability_categories.items()
        },
    )


def _build_alias_map(categories: dict[str, dict[str, list[str]]]) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for category_slug, payload in categories.items():
        for alias in payload.get("aliases", []):
            alias_map[_normalize_key(alias)] = category_slug
    return alias_map


def _normalize_key(value: str) -> str:
    return value.strip().lower()
