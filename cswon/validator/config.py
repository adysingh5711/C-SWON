# C-SWON Validator Configuration
# All scoring constants and version strings per readme.md

"""
Validator-specific configuration constants for C-SWON.
All values are directly referenced from the readme.md specification.
"""

# ── Scoring Version (readme §4.5) ──────────────────────────────────
SCORING_VERSION = "1.0.0"
# Encode as integer: major*10000 + minor*100 + patch
__spec_version__ = 10000  # "1.0.0" → 1*10000 + 0*100 + 0

# ── Tempo & Weight Submission (readme §4.1, §4.9) ──────────────────
TEMPO = 360  # blocks per tempo (~72 minutes)

# ── Scoring Formula Weights (readme §2.2) ───────────────────────────
SCORE_WEIGHTS = {
    "success":     0.50,
    "cost":        0.25,
    "latency":     0.15,
    "reliability": 0.10,
}

# Success gate: cost and latency only scored when S_success > this
SUCCESS_GATE = 0.70

# ── Score Aggregation (readme §2.2, §4.8 step 6) ───────────────────
SCORE_WINDOW_SIZE = 100         # rolling N-task window, equal weight
MAX_MINER_WEIGHT_FRACTION = 0.15  # 15% cap per miner before submission

# ── Immunity & Warm-Up (readme §4.4) ────────────────────────────────
WARMUP_TASK_THRESHOLD = 20      # tasks seen before full weight influence

# ── Execution Support (readme §4.6) ─────────────────────────────────
EXEC_SUPPORT_N_MIN = 30         # min tasks per tempo for exec support eligibility

# ── Query Loop (readme §4.1) ────────────────────────────────────────
QUERY_TIMEOUT_S = 9             # hard ceiling: must be < 12 s (1 block)

# ── Early Participation Programme (readme §3.5) ─────────────────────
EARLY_MINER_BOOST_MULTIPLIER = 3   # 3× query frequency for early miners
EARLY_MINER_LIMIT = 50             # first 50 registered miners

# ── Reliability Scoring Penalties (readme §2.2) ─────────────────────
RELIABILITY_UNPLANNED_RETRY_PENALTY = 0.10
RELIABILITY_TIMEOUT_PENALTY = 0.20
RELIABILITY_HARD_FAILURE_PENALTY = 0.50

# ── Benchmark Governance (readme §4.7) ──────────────────────────────
DEPRECATION_SCORE_THRESHOLD = 0.90   # >70% miners scoring above this
QUARANTINE_SCORE_THRESHOLD = 0.10    # >70% miners scoring below this
DEPRECATION_TEMPO_COUNT = 3          # consecutive tempos for trigger
QUARANTINE_REMOVAL_TEMPOS = 5        # tempos before auto-removal

# ── Benchmark Path ──────────────────────────────────────────────────
import os
BENCHMARK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "benchmarks",
    "v1.json",
)
