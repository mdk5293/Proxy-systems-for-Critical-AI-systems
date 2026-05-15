"""Pure numeric helpers aligned with REDUX_4 notebook patch cell."""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def contrastive_adjust(
    raw_score: float,
    neg_scores: Sequence[float],
    *,
    temperature: float = 6.0,
) -> float:
    """Sigmoid of ``raw_score - median(neg_scores)`` scaled by ``temperature``."""
    if not neg_scores:
        return float(raw_score)
    ns = sorted(float(x) for x in neg_scores)
    mid = len(ns) // 2
    if len(ns) % 2 == 1:
        baseline = ns[mid]
    else:
        baseline = 0.5 * (ns[mid - 1] + ns[mid])
    delta = float(raw_score) - baseline
    t = float(temperature)
    return float(1.0 / (1.0 + math.exp(-t * delta)))


def rank_fraction(sorted_urls: List[str], target_url: str) -> float:
    """0 = best rank, 1 = worst (same ordering as ``_metadata_rank_pct_display`` / n-1)."""
    if not sorted_urls:
        return 0.0
    if target_url not in sorted_urls:
        return 0.0
    n = len(sorted_urls)
    if n <= 1:
        return 1.0
    idx = sorted_urls.index(target_url)
    return float(1.0 - idx / (n - 1))


def winsor_bounds(values: List[float], q_low: float = 0.05, q_high: float = 0.95) -> Tuple[float, float]:
    """Return (lo, hi) quantile bounds; requires numpy-free path for tiny lists."""
    if len(values) < 3:
        return min(values), max(values)
    xs = sorted(float(x) for x in values)
    i_lo = int(round((len(xs) - 1) * q_low))
    i_hi = int(round((len(xs) - 1) * q_high))
    i_lo = max(0, min(i_lo, len(xs) - 1))
    i_hi = max(0, min(i_hi, len(xs) - 1))
    return xs[i_lo], xs[i_hi]
