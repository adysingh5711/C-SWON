#!/usr/bin/env python3
# C-SWON Validator — Docker Container Entry Point
# Called by docker_sandbox.py via: python -m cswon.validator.executor_entrypoint
# See readme §4.8 step 3 and docker_sandbox.py line 121.

"""
Docker container entry point for sandboxed workflow execution.

Contract (readme §4.8 step 3):
  - Reads  CSWON_WORKFLOW_PAYLOAD (JSON string) from the environment.
  - Calls  execute_workflow() with the parsed payload.
  - Prints the ExecutionResult serialised as JSON to **stdout**.
  - Exits  0 on success, 1 on any error.

The docker_sandbox._parse_exec_result_json() function parses the stdout JSON
back into an ExecutionResult on the host side.

Environment variables consumed:
  CSWON_WORKFLOW_PAYLOAD   – JSON object with keys:
                               workflow_plan, constraints, total_estimated_cost,
                               partner_hotkey (optional)
  CSWON_MOCK_EXEC          – "false" in live mode (set by docker_sandbox.py)
  CSWON_PARTNER_HOTKEY     – Validator's registered hotkey on partner subnets
"""

import json
import os
import sys


def main() -> None:
    # ── 1. Read payload from environment ────────────────────────────────────
    payload_str = os.environ.get("CSWON_WORKFLOW_PAYLOAD", "").strip()
    if not payload_str:
        print(
            json.dumps({"error": "CSWON_WORKFLOW_PAYLOAD environment variable is not set"}),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as exc:
        print(
            json.dumps({"error": f"Failed to parse CSWON_WORKFLOW_PAYLOAD: {exc}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    workflow_plan = payload.get("workflow_plan")
    constraints = payload.get("constraints", {})
    total_estimated_cost = float(payload.get("total_estimated_cost", 0.01))
    routing_policy = payload.get("routing_policy", {})

    if workflow_plan is None:
        print(
            json.dumps({"error": "CSWON_WORKFLOW_PAYLOAD missing 'workflow_plan' key"}),
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 2. Execute the workflow ──────────────────────────────────────────────
    # Import here (after env check) so import errors don't swallow the real error.
    try:
        from cswon.validator.executor import execute_workflow  # type: ignore
    except ImportError as exc:
        print(
            json.dumps({"error": f"Cannot import executor module: {exc}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = execute_workflow(
            workflow_plan=workflow_plan,
            constraints=constraints,
            total_estimated_cost=total_estimated_cost,
            mock_mode=False,          # always False inside the Docker container
            routing_policy=routing_policy,
        )
    except Exception as exc:
        # Surface the error as a valid JSON payload so host side can parse it
        print(
            json.dumps({"error": f"execute_workflow raised: {exc}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 3. Serialise ExecutionResult to stdout ───────────────────────────────
    output = {
        "actual_cost":       result.actual_cost,
        "actual_latency":    result.actual_latency,
        "steps_completed":   result.steps_completed,
        "total_steps":       result.total_steps,
        "timeouts":          result.timeouts,
        "hard_failures":     result.hard_failures,
        "unplanned_retries": result.unplanned_retries,
        "budget_aborted":    result.budget_aborted,
        "final_output":      result.final_output,
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
