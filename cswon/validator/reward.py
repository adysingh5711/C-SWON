# C-SWON Validator — Reward / Scoring Module
# Implements the four-dimension scoring formula (readme §2.2)
# and output quality scoring by task type (readme §2.3).

"""
Composite scoring engine for C-SWON validators.

S = 0.50 × S_success + 0.25 × S_cost + 0.15 × S_latency + 0.10 × S_reliability
"""

import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict

import bittensor as bt

from cswon.validator.config import (
    SCORE_WEIGHTS,
    SUCCESS_GATE,
    WARMUP_TASK_THRESHOLD,
    SCORE_WINDOW_SIZE,
    MAX_MINER_WEIGHT_FRACTION,
    RELIABILITY_UNPLANNED_RETRY_PENALTY,
    RELIABILITY_TIMEOUT_PENALTY,
    RELIABILITY_HARD_FAILURE_PENALTY,
)


# ── Output Quality Scoring (readme §2.3) ───────────────────────────

def score_output_quality(
    task_type: str,
    output: Optional[dict],
    reference: dict,
) -> float:
    """
    Score output quality by task type using deterministic methods (readme §2.3).
    No LLM judge in v1 — all scoring is reference-based.

    Args:
        task_type: One of "code", "rag", "agent", "data_transform".
        output: The workflow's final output dict.
        reference: Reference data from benchmark task (test suite, reference answer, etc.).

    Returns:
        float: output_quality_score in [0, 1].
    """
    if output is None:
        return 0.0

    output_text = output.get("text", "")
    output_code = output.get("artifacts", {}).get("code", "")

    if task_type == "code":
        return _score_code_quality(output_code, reference)
    elif task_type == "rag":
        return _score_rag_quality(output_text, reference)
    elif task_type == "agent":
        return _score_agent_quality(output, reference)
    elif task_type == "data_transform":
        return _score_data_transform_quality(output, reference)
    else:
        bt.logging.warning(f"Unknown task type '{task_type}', defaulting to 0.0")
        return 0.0


def _score_code_quality(code_output: str, reference: dict) -> float:
    """
    Code quality: automated test pass rate + PEP8 linting (readme §2.3, issue 2.5).
    Runs pytest and pycodestyle in a subprocess for real scoring.
    Falls back to pattern-matching if tools unavailable.
    """
    import pathlib, subprocess, tempfile

    if not code_output:
        return 0.0

    test_suite = reference.get("test_suite", "")
    expected_patterns = reference.get("expected_patterns", [])

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = pathlib.Path(tmpdir) / "solution.py"
            code_file.write_text(code_output)

            # --- Test pass rate ---
            test_score = 0.5
            if test_suite:
                test_file = pathlib.Path(tmpdir) / "test_solution.py"
                test_file.write_text(test_suite)
                r = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-q", "--tb=no"],
                    capture_output=True, text=True, timeout=15,
                )
                test_score = _parse_pytest_fraction(r.stdout)

            # --- PEP8 linting score ---
            lint_score = 1.0
            r2 = subprocess.run(
                ["python", "-m", "pycodestyle", "--max-line-length=100", str(code_file)],
                capture_output=True, text=True, timeout=10,
            )
            violations = len([l for l in r2.stdout.strip().split("\n") if l.strip()])
            lint_score = max(0.0, 1.0 - violations * 0.05)

            return 0.7 * test_score + 0.3 * lint_score

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        bt.logging.warning("Code test runner unavailable; falling back to pattern match")

    # Fallback: expected_patterns keyword check
    if not expected_patterns:
        return 0.5
    matches = sum(1 for p in expected_patterns if p in code_output)
    return matches / len(expected_patterns)


def _parse_pytest_fraction(output: str) -> float:
    """Parse pytest summary line (e.g. '3 passed, 1 failed') → fraction passed."""
    import re
    passed = sum(int(m) for m in re.findall(r'(\d+) passed', output))
    failed = sum(int(m) for m in re.findall(r'(\d+) failed', output))
    total = passed + failed
    return passed / total if total > 0 else 0.5


def _score_rag_quality(output_text: str, reference: dict) -> float:
    """
    RAG quality: ROUGE-L F1 against reference answer (readme §2.3).
    ROUGE-L measures longest common subsequence overlap.
    """
    reference_answer = reference.get("reference_answer", "")
    if not reference_answer or not output_text:
        return 0.0

    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference_answer, output_text)
        return scores["rougeL"].fmeasure
    except ImportError:
        bt.logging.warning("rouge-score not installed, using fallback LCS scoring")
        return _lcs_f1(reference_answer, output_text)


def _lcs_f1(reference: str, hypothesis: str) -> float:
    """Fallback LCS-based F1 score if rouge-score is not available."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if not ref_words or not hyp_words:
        return 0.0

    # LCS via dynamic programming
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    precision = lcs_len / n if n > 0 else 0
    recall = lcs_len / m if m > 0 else 0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _score_agent_quality(output: dict, reference: dict) -> float:
    """
    Agent quality: structured binary pass/fail per criterion (readme §2.3, issue 2.6).
    Score = passed / total criteria.

    Each criterion may have a 'type':
      'keyword' (default): exact text must appear in output
      'json_key': output must be parseable JSON containing the specified key
      'regex': output must match the provided 'pattern'
    """
    import re as _re, json as _json

    checklist = reference.get("goal_checklist", [])
    if not checklist:
        return 0.5

    output_text = str(output.get("text", ""))
    output_lower = output_text.lower()

    def _check(criterion: dict) -> bool:
        ctype = criterion.get("type", "keyword")
        text  = criterion.get("text", "").lower()
        if ctype == "keyword":
            return text in output_lower
        elif ctype == "json_key":
            try:
                parsed = _json.loads(output_text)
                return text in (parsed if isinstance(parsed, dict) else {})
            except Exception:
                return False
        elif ctype == "regex":
            pattern = criterion.get("pattern", "")
            return bool(_re.search(pattern, output_text, _re.IGNORECASE))
        return False

    passed = sum(1 for c in checklist if _check(c))
    return passed / len(checklist)


def _score_data_transform_quality(output: dict, reference: dict) -> float:
    """
    Data transform quality: schema validation + exact-match (readme §2.3).
    """
    expected_output = reference.get("expected_output")
    if expected_output is None:
        return 0.5

    actual = output.get("text", "")
    if isinstance(expected_output, str):
        return 1.0 if actual.strip() == expected_output.strip() else 0.0

    # For dict/structured comparison
    if isinstance(expected_output, dict):
        try:
            import json
            actual_parsed = json.loads(actual) if isinstance(actual, str) else actual
            return 1.0 if actual_parsed == expected_output else 0.0
        except (json.JSONDecodeError, TypeError):
            return 0.0

    return 0.0


# ── Four-Dimension Composite Scoring (readme §2.2) ─────────────────

def compute_composite_score(
    output_quality: float,
    completion_ratio: float,
    actual_cost: float,
    max_budget: float,
    actual_latency: float,
    max_latency: float,
    unplanned_retries: int,
    timeouts: int,
    hard_failures: int,
    budget_aborted: bool = False,
) -> Dict[str, float]:
    """
    Compute the four-dimension composite score (readme §2.2).

    S = 0.50 × S_success + 0.25 × S_cost + 0.15 × S_latency + 0.10 × S_reliability

    Args:
        output_quality: Output quality score from score_output_quality().
        completion_ratio: steps_completed / total_steps_in_dag.
        actual_cost: Actual TAO consumed.
        max_budget: Maximum budget TAO from constraints.
        actual_latency: Actual wall-clock seconds.
        max_latency: Maximum latency seconds from constraints.
        unplanned_retries: Retries beyond declared budget.
        timeouts: Timeout events.
        hard_failures: Hard failure events.
        budget_aborted: Whether the workflow was budget-aborted.

    Returns:
        Dict with keys: "S_success", "S_cost", "S_latency", "S_reliability", "S_composite"
    """
    # S_success = output_quality × completion_ratio
    s_success = output_quality * completion_ratio

    # S_cost: gated at S_success > 0.7; forced to 0 on budget abort
    if budget_aborted:
        s_cost = 0.0
    elif s_success > SUCCESS_GATE and max_budget > 0:
        s_cost = max(0.0, 1.0 - actual_cost / max_budget)
    else:
        s_cost = 0.0

    # S_latency: gated at S_success > 0.7
    if s_success > SUCCESS_GATE and max_latency > 0:
        s_latency = max(0.0, 1.0 - actual_latency / max_latency)
    else:
        s_latency = 0.0

    # S_reliability = min(1.0, max(0, 1 - unplanned×0.10 - timeouts×0.20 - failures×0.50))
    # Applied regardless of success gate
    reliability_penalty = (
        unplanned_retries * RELIABILITY_UNPLANNED_RETRY_PENALTY
        + timeouts * RELIABILITY_TIMEOUT_PENALTY
        + hard_failures * RELIABILITY_HARD_FAILURE_PENALTY
    )
    s_reliability = min(1.0, max(0.0, 1.0 - reliability_penalty))

    # Composite score
    s_composite = (
        SCORE_WEIGHTS["success"] * s_success
        + SCORE_WEIGHTS["cost"] * s_cost
        + SCORE_WEIGHTS["latency"] * s_latency
        + SCORE_WEIGHTS["reliability"] * s_reliability
    )

    return {
        "S_success": s_success,
        "S_cost": s_cost,
        "S_latency": s_latency,
        "S_reliability": s_reliability,
        "S_composite": s_composite,
    }


# ── Immunity Warm-Up Scale (readme §4.4) ───────────────────────────

def get_miner_weight(
    miner_uid: int,
    tasks_seen: int,
    raw_score: float,
    subtensor: "bt.subtensor",
    netuid: int,
    current_block: int,
) -> float:
    """
    Apply immunity warm-up scale to miner weights (readme §4.4).

    New miners receive immunity_period of 5,000 blocks (~16.7 hours).
    During this window, weight = raw_score × min(1.0, tasks_seen / WARMUP_TASK_THRESHOLD).
    Once 20 tasks seen, miner has full weight influence.
    """
    try:
        immunity_period = subtensor.get_subnet_hyperparameters(netuid).immunity_period
        neuron_info = subtensor.neuron_for_uid(uid=miner_uid, netuid=netuid)
        reg_block = neuron_info.block
        blocks_since_reg = current_block - reg_block
        is_immune = blocks_since_reg < immunity_period
    except Exception:
        # If we can't get chain data, assume not immune
        is_immune = False

    if is_immune:
        warmup_scale = min(1.0, tasks_seen / WARMUP_TASK_THRESHOLD)
        return raw_score * warmup_scale

    return raw_score


# ── Rolling Window Score Aggregation (readme §2.2) ─────────────────

class ScoreAggregator:
    """
    Maintains a rolling N-task equal-weight window per miner (readme §2.2).
    Applies 15% max weight cap per miner before submission (readme §4.8 step 6).
    """

    def __init__(self, window_size: int = SCORE_WINDOW_SIZE):
        self.window_size = window_size
        # miner_uid -> list of recent scores (most recent last)
        self.score_windows: Dict[int, List[float]] = defaultdict(list)
        # miner_uid -> number of tasks seen (for warmup)
        self.tasks_seen: Dict[int, int] = defaultdict(int)

    def add_score(self, miner_uid: int = None, score: float = 0.0, *, uid: int = None):
        """Add a score to a miner's rolling window.

        Accepts both ``miner_uid`` (canonical) and ``uid`` (test-suite alias)
        as positional-or-keyword arguments to maintain backward compatibility.
        """
        # Resolve uid alias — uid= takes precedence if miner_uid is unset
        resolved_uid = miner_uid if miner_uid is not None else uid
        if resolved_uid is None:
            raise TypeError("add_score() requires miner_uid or uid argument")
        window = self.score_windows[resolved_uid]
        window.append(score)
        if len(window) > self.window_size:
            window.pop(0)  # remove oldest
        self.tasks_seen[resolved_uid] += 1

    def get_average_score(self, miner_uid: int) -> float:
        """Get equal-weight average score for a miner."""
        window = self.score_windows.get(miner_uid, [])
        if not window:
            return 0.0
        return sum(window) / len(window)

    def get_normalised_weights(
        self, miner_uids: List[int]
    ) -> Dict[int, float]:
        """
        Get normalised weights with 15% per-miner cap (readme §4.8 step 6).
        """
        raw_weights = {}
        for uid in miner_uids:
            raw_weights[uid] = self.get_average_score(uid)

        total = sum(raw_weights.values())
        if total == 0:
            return {uid: 0.0 for uid in miner_uids}

        # Normalise
        normalised = {uid: w / total for uid, w in raw_weights.items()}

        # Apply 15% cap — redistribute excess
        capped = _apply_weight_cap(normalised, MAX_MINER_WEIGHT_FRACTION)
        return capped


def _apply_weight_cap(
    weights: Dict[int, float], max_fraction: float
) -> Dict[int, float]:
    """Apply per-miner weight cap and redistribute excess."""
    capped = {}
    excess = 0.0
    uncapped_uids = []

    for uid, w in weights.items():
        if w > max_fraction:
            capped[uid] = max_fraction
            excess += w - max_fraction
        else:
            capped[uid] = w
            uncapped_uids.append(uid)

    # Redistribute excess proportionally to uncapped miners
    if excess > 0 and uncapped_uids:
        uncapped_total = sum(capped[uid] for uid in uncapped_uids)
        if uncapped_total > 0:
            for uid in uncapped_uids:
                share = capped[uid] / uncapped_total
                capped[uid] += excess * share

    # Final normalisation to ensure sum = 1.0
    total = sum(capped.values())
    if total > 0:
        capped = {uid: w / total for uid, w in capped.items()}

    return capped
