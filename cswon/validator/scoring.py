"""Alias module — readme §4.4/4.5 references validator/scoring.py. (issue 3.1)"""
from cswon.validator.config import (
    SCORING_VERSION,
    WARMUP_TASK_THRESHOLD,
    __spec_version__,
    SCORE_WEIGHTS,
    SCORE_WINDOW_SIZE,
    MAX_MINER_WEIGHT_FRACTION,
)
from cswon.validator.reward import compute_composite_score, ScoreAggregator, get_miner_weight

__all__ = [
    "SCORING_VERSION",
    "WARMUP_TASK_THRESHOLD",
    "__spec_version__",
    "SCORE_WEIGHTS",
    "SCORE_WINDOW_SIZE",
    "MAX_MINER_WEIGHT_FRACTION",
    "compute_composite_score",
    "ScoreAggregator",
    "get_miner_weight",
]
