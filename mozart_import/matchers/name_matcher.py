# mozart_import/matchers/name_matcher.py
from difflib import SequenceMatcher
from typing import Tuple, Optional


class NameMatcher:
    """Сопоставление по имени (таблиц, полей)."""

    @staticmethod
    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def best_match(name: str, candidates: list, threshold: float = 0.6) -> Tuple[Optional[str], float]:
        best = None
        best_score = 0.0
        for cand in candidates:
            score = NameMatcher.similarity(name, cand)
            if score > best_score:
                best_score = score
                best = cand
        if best_score >= threshold:
            return best, best_score
        return None, 0.0