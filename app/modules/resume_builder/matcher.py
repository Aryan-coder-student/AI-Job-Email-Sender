from __future__ import annotations

import re
from collections import Counter

from app.modules.resume_builder.model import JobRequirements, ProfessionalProfile, Recommendation

STOP_WORDS = {"and", "the", "with", "for", "from", "that", "this", "you", "your", "our", "are", "will", "have", "has", "into", "using", "years", "work", "role"}


class KeywordRecommendationEngine:
    """Deterministic baseline; can be replaced by an LLM adapter without changing callers."""

    def recommend(self, profile: ProfessionalProfile, job: JobRequirements, limit: int) -> list[Recommendation]:
        targets = self._terms(" ".join([job.role, job.description, *job.required_skills, *job.keywords]))
        weighted_targets = Counter(targets)
        for skill in job.required_skills:
            weighted_targets.update(self._terms(skill) * 2)

        recommendations: list[Recommendation] = []
        for section in ("experiences", "projects", "certifications", "publications"):
            for item in getattr(profile, section):
                terms = set(self._terms(" ".join([item.title, item.subtitle, item.description, *item.skills])))
                matched = sorted(terms.intersection(weighted_targets), key=lambda term: (-weighted_targets[term], term))
                coverage = sum(weighted_targets[term] for term in matched)
                denominator = max(sum(weighted_targets.values()), 1)
                score = min(1.0, coverage / denominator * 3)
                recommendations.append(Recommendation(
                    item_id=item.id,
                    section=section,
                    title=item.title,
                    score=round(score, 4),
                    matched_keywords=matched[:8],
                    reason=(f"Matches {', '.join(matched[:5])}." if matched else "Included as supporting profile evidence."),
                ))
        recommendations.sort(key=lambda item: (-item.score, item.section, item.title.lower()))
        return recommendations[:limit]

    @staticmethod
    def _terms(value: str) -> list[str]:
        return [term for term in re.findall(r"[a-z0-9+#.]{2,}", value.lower()) if term not in STOP_WORDS]
