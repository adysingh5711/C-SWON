# C-SWON Validator — Docker Sandbox
# Wraps workflow execution inside an isolated Docker container (readme §2.5, §4.8 step 3).

"""
Sandboxed execution helper.

When CSWON_MOCK_EXEC=false, workflows are executed inside a Docker container
for isolation. This module handles container lifecycle management.

When CSWON_MOCK_EXEC=true (default on testnet), Docker is bypassed and the
mock executor is used directly — no real subnet calls, no TAO burned.
"""

import json
import os
import subprocess
import tempfile
from typing import Optional

import bittensor as bt

from cswon.validator.executor import execute_workflow, ExecutionResult

# Docker image that contains this repo's executor runtime.
# Build with: docker build -t cswon-executor:latest .
DOCKER_IMAGE = os.environ.get("CSWON_DOCKER_IMAGE", "cswon-executor:latest")

# Wall-clock timeout multiplier: sandbox gets max_latency * this factor.
SANDBOX_TIMEOUT_MULTIPLIER = 1.5


def run_workflow_in_sandbox(
    workflow_plan: dict,
    constraints: dict,
    total_estimated_cost: float,
    partner_hotkey: Optional[str] = None,
    mock_mode: Optional[bool] = None,
) -> ExecutionResult:
    """
    Execute a miner's workflow plan in an isolated sandbox (readme §4.8 step 3).

    In mock mode (CSWON_MOCK_EXEC=true): calls execute_workflow() directly.
    In live mode (CSWON_MOCK_EXEC=false): spins up a Docker container, passes
    the workflow payload into it as JSON, and captures the ExecutionResult.

    Args:
        workflow_plan: Dict with "nodes", "edges", "error_handling".
        constraints: Dict with "max_budget_tao", "max_latency_seconds".
        total_estimated_cost: Miner's declared total estimated cost.
        partner_hotkey: Validator's registered hotkey on partner subnets.
        mock_mode: If None, reads from CSWON_MOCK_EXEC env var.

    Returns:
        ExecutionResult with all tracked metrics.
    """
    if mock_mode is None:
        mock_mode = os.environ.get("CSWON_MOCK_EXEC", "true").lower() == "true"

    if mock_mode:
        # ── Mock path: no Docker, no real subnet calls ────────────────────
        return execute_workflow(
            workflow_plan=workflow_plan,
            constraints=constraints,
            total_estimated_cost=total_estimated_cost,
            mock_mode=True,
        )

    # ── Live path: run inside Docker container ────────────────────────────
    return _docker_execute(
        workflow_plan=workflow_plan,
        constraints=constraints,
        total_estimated_cost=total_estimated_cost,
        partner_hotkey=partner_hotkey,
    )


def _check_docker_cli() -> bool:
    """Check Docker CLI is on PATH and the daemon is reachable."""
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _docker_execute(
    workflow_plan: dict,
    constraints: dict,
    total_estimated_cost: float,
    partner_hotkey: Optional[str],
) -> ExecutionResult:
    """
    Spin up a Docker container, run the workflow, and parse the result.

    The container is expected to:
      1. Read workflow JSON from the CSWON_WORKFLOW_PAYLOAD environment variable.
      2. Execute it using the same execute_workflow() function.
      3. Print the ExecutionResult as JSON to stdout.
      4. Exit 0 on success.

    Falls back to mock mode gracefully if Docker is not available or the
    container fails to start.
    """
    if not _check_docker_cli():
        bt.logging.error(
            "Docker CLI not available or daemon not running. "
            "Install Docker 24.x+ or set CSWON_MOCK_EXEC=true for testnet."
        )
        return _fallback_mock(workflow_plan, constraints, total_estimated_cost)

    max_latency = constraints.get("max_latency_seconds", 30.0)
    timeout_s = max_latency * SANDBOX_TIMEOUT_MULTIPLIER

    payload = json.dumps({
        "workflow_plan": workflow_plan,
        "constraints": constraints,
        "total_estimated_cost": total_estimated_cost,
        "partner_hotkey": partner_hotkey,
    })

    bt.logging.info(
        f"Launching Docker sandbox: image={DOCKER_IMAGE} "
        f"timeout={timeout_s:.1f}s"
    )

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network=none",          # no network access inside sandbox
                "--memory=512m",           # tighter memory cap
                "--cpus=1",
                "--read-only",             # read-only filesystem
                "--tmpfs=/tmp:size=64m",   # only allow writes to /tmp
                f"--env=CSWON_MOCK_EXEC=false",
                f"--env=CSWON_PARTNER_HOTKEY={partner_hotkey or ''}",
                f"--env=CSWON_WORKFLOW_PAYLOAD={payload}",
                DOCKER_IMAGE,
                "python", "-m", "cswon.validator.executor_entrypoint",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        if result.returncode != 0:
            bt.logging.error(
                f"Docker sandbox exited with code {result.returncode}. "
                f"stderr: {result.stderr[:500]}"
            )
            return _fallback_mock(workflow_plan, constraints, total_estimated_cost)

        # Parse the ExecutionResult JSON from stdout
        return _parse_exec_result_json(result.stdout)

    except subprocess.TimeoutExpired:
        bt.logging.warning(
            f"Docker sandbox timed out after {timeout_s:.1f}s "
            f"— marking all steps as timeout failures."
        )
        return _timeout_result(workflow_plan)

    except FileNotFoundError:
        bt.logging.error(
            "Docker not found on PATH. Set CSWON_MOCK_EXEC=true for testnet, "
            "or install Docker 24.x+ for live execution."
        )
        return _fallback_mock(workflow_plan, constraints, total_estimated_cost)

    except Exception as e:
        bt.logging.error(f"Unexpected Docker sandbox error: {e}")
        return _fallback_mock(workflow_plan, constraints, total_estimated_cost)


def _parse_exec_result_json(stdout: str) -> ExecutionResult:
    """Parse executor container stdout as an ExecutionResult."""
    try:
        data = json.loads(stdout.strip())
        result = ExecutionResult()
        result.actual_cost = float(data.get("actual_cost", 0.0))
        result.actual_latency = float(data.get("actual_latency", 0.0))
        result.steps_completed = int(data.get("steps_completed", 0))
        result.total_steps = int(data.get("total_steps", 0))
        result.timeouts = int(data.get("timeouts", 0))
        result.hard_failures = int(data.get("hard_failures", 0))
        result.unplanned_retries = int(data.get("unplanned_retries", 0))
        result.budget_aborted = bool(data.get("budget_aborted", False))
        result.final_output = data.get("final_output")
        return result
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        bt.logging.error(f"Failed to parse Docker executor output: {e}")
        result = ExecutionResult()
        result.hard_failures = 1
        return result


def _fallback_mock(workflow_plan, constraints, total_estimated_cost) -> ExecutionResult:
    """Fallback to mock execution when Docker is unavailable."""
    bt.logging.warning("Falling back to mock execution (Docker unavailable).")
    return execute_workflow(
        workflow_plan=workflow_plan,
        constraints=constraints,
        total_estimated_cost=total_estimated_cost,
        mock_mode=True,
    )


def _timeout_result(workflow_plan: dict) -> ExecutionResult:
    """Return an ExecutionResult representing a full timeout of the sandbox."""
    result = ExecutionResult()
    nodes = workflow_plan.get("nodes", [])
    result.total_steps = len(nodes)
    result.timeouts = len(nodes)
    result.steps_completed = 0
    return result
