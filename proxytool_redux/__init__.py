"""Thin mirror of REDUX_4 scoring helpers for tests and optional imports from scripts.

The canonical implementation remains in ``proxytool_REDUX_4.ipynb`` (patch cell ``893d6fab``).
"""

from proxytool_redux.scoring import contrastive_adjust, rank_fraction, winsor_bounds

__all__ = ["contrastive_adjust", "rank_fraction", "winsor_bounds"]
