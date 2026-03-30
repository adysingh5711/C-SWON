#!/usr/bin/env python3
"""
C-SWON Benchmark Generator — v1.json

Generates a 60-task benchmark dataset satisfying readme §4.7:
  - >= 50 active tasks
  - 15–20% synthetic (type="synthetic")
  - Task types: code (13), rag (12), agent (13), data_transform (12), synthetic (10)
  - Each task has: task_id, task_type, status, description, quality_criteria,
    constraints, available_tools, routing_policy, reference

Usage:
    python scripts/generate_benchmarks.py > benchmarks/v1.json
"""

import json
import sys

# ── Subnet tool definitions ───────────────────────────────────────────────────

TOOLS_SN1 = {"sn1": {"type": "text_generation", "avg_cost": 0.001, "avg_latency": 0.5}}
TOOLS_SN4 = {"sn4": {"type": "code_generation", "avg_cost": 0.003, "avg_latency": 1.2}}
TOOLS_SN13 = {"sn13": {"type": "data_processing", "avg_cost": 0.002, "avg_latency": 0.8}}
TOOLS_SN18 = {"sn18": {"type": "inference", "avg_cost": 0.0005, "avg_latency": 0.3}}
TOOLS_SN22 = {"sn22": {"type": "web_access", "avg_cost": 0.002, "avg_latency": 1.0}}

TOOLS_SN1_SN4 = {**TOOLS_SN1, **TOOLS_SN4}
TOOLS_SN1_SN13 = {**TOOLS_SN1, **TOOLS_SN13}
TOOLS_SN1_SN22 = {**TOOLS_SN1, **TOOLS_SN22}
TOOLS_SN4_SN13 = {**TOOLS_SN4, **TOOLS_SN13}
TOOLS_SN1_SN4_SN13 = {**TOOLS_SN1, **TOOLS_SN4, **TOOLS_SN13}
TOOLS_SN1_SN18 = {**TOOLS_SN1, **TOOLS_SN18}
TOOLS_SN13_SN18 = {**TOOLS_SN13, **TOOLS_SN18}

# ── Routing policy helpers ────────────────────────────────────────────────────

def routing(top_k=3, aggregation="majority_vote", miner_selection="top_k_stake_weighted"):
    return {
        "default": {
            "miner_selection": miner_selection,
            "top_k": top_k,
            "aggregation": aggregation,
        }
    }


# ── Task builder helpers ──────────────────────────────────────────────────────

def code_task(
    task_id,
    description,
    test_suite,
    expected_patterns,
    allowed_subnets,
    available_tools,
    max_budget=0.02,
    max_latency=15,
    top_k=3,
    quality_criteria=None,
    status="active",
):
    return {
        "task_id": task_id,
        "task_type": "code",
        "status": status,
        "description": description,
        "quality_criteria": quality_criteria or {"min_test_pass_rate": 0.8},
        "constraints": {
            "max_budget_tao": max_budget,
            "max_latency_seconds": max_latency,
            "allowed_subnets": allowed_subnets,
        },
        "available_tools": available_tools,
        "routing_policy": routing(top_k=top_k),
        "reference": {
            "test_suite": test_suite,
            "expected_patterns": expected_patterns,
        },
    }


def rag_task(
    task_id,
    description,
    reference_answer,
    allowed_subnets,
    available_tools,
    max_budget=0.01,
    max_latency=10,
    top_k=3,
    quality_criteria=None,
    status="active",
):
    return {
        "task_id": task_id,
        "task_type": "rag",
        "status": status,
        "description": description,
        "quality_criteria": quality_criteria or {"min_rouge_l": 0.3},
        "constraints": {
            "max_budget_tao": max_budget,
            "max_latency_seconds": max_latency,
            "allowed_subnets": allowed_subnets,
        },
        "available_tools": available_tools,
        "routing_policy": routing(top_k=top_k),
        "reference": {
            "reference_answer": reference_answer,
        },
    }


def agent_task(
    task_id,
    description,
    goal_checklist,
    allowed_subnets,
    available_tools,
    max_budget=0.015,
    max_latency=20,
    top_k=3,
    quality_criteria=None,
    status="active",
):
    return {
        "task_id": task_id,
        "task_type": "agent",
        "status": status,
        "description": description,
        "quality_criteria": quality_criteria or {"min_checklist_pass_rate": 0.8},
        "constraints": {
            "max_budget_tao": max_budget,
            "max_latency_seconds": max_latency,
            "allowed_subnets": allowed_subnets,
        },
        "available_tools": available_tools,
        "routing_policy": routing(top_k=top_k),
        "reference": {
            "goal_checklist": goal_checklist,
        },
    }


def data_task(
    task_id,
    description,
    expected_output,
    allowed_subnets,
    available_tools,
    max_budget=0.005,
    max_latency=8,
    top_k=3,
    quality_criteria=None,
    status="active",
):
    return {
        "task_id": task_id,
        "task_type": "data_transform",
        "status": status,
        "description": description,
        "quality_criteria": quality_criteria or {"exact_match": True},
        "constraints": {
            "max_budget_tao": max_budget,
            "max_latency_seconds": max_latency,
            "allowed_subnets": allowed_subnets,
        },
        "available_tools": available_tools,
        "routing_policy": routing(top_k=top_k),
        "reference": {
            "expected_output": expected_output,
        },
    }


def synthetic_task(base, task_id, description, optimal_workflow=None):
    """Wrap an existing task dict as a synthetic variant."""
    t = dict(base)
    t["task_id"] = task_id
    t["description"] = description
    t["type"] = "synthetic"
    if optimal_workflow is not None:
        t["reference"] = dict(t["reference"])
        t["reference"]["optimal_workflow"] = optimal_workflow
    return t


# ── Optimal workflow helpers ──────────────────────────────────────────────────

def workflow(*steps):
    """Build a linear optimal_workflow DAG from step tuples (id, subnet, action)."""
    nodes = [{"id": s[0], "subnet": s[1], "action": s[2]} for s in steps]
    edges = [{"from": steps[i][0], "to": steps[i + 1][0]} for i in range(len(steps) - 1)]
    return {"nodes": nodes, "edges": edges}


# ═════════════════════════════════════════════════════════════════════════════
# CODE TASKS  (13 total)
# ═════════════════════════════════════════════════════════════════════════════

CODE_TASKS = [
    code_task(
        task_id="code_001",
        description="Implement a Python function that merges two sorted lists into one sorted list without using built-in sort.",
        test_suite=(
            "def test_merge():\n"
            "    from solution import merge_sorted\n"
            "    assert merge_sorted([1,3,5],[2,4,6]) == [1,2,3,4,5,6]\n"
            "    assert merge_sorted([],[1]) == [1]\n"
            "    assert merge_sorted([],[]) == []"
        ),
        expected_patterns=["def merge_sorted", "while", "append"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
    ),
    code_task(
        task_id="code_002",
        description="Implement a binary search function that returns the index of a target in a sorted list, or -1 if not found.",
        test_suite=(
            "def test_binary_search():\n"
            "    from solution import binary_search\n"
            "    assert binary_search([1,3,5,7,9], 5) == 2\n"
            "    assert binary_search([1,3,5,7,9], 4) == -1\n"
            "    assert binary_search([], 1) == -1\n"
            "    assert binary_search([42], 42) == 0"
        ),
        expected_patterns=["def binary_search", "mid", "low", "high"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.02,
        max_latency=12,
    ),
    code_task(
        task_id="code_003",
        description="Implement a function that checks whether a given string is a valid palindrome, ignoring spaces and case.",
        test_suite=(
            "def test_palindrome():\n"
            "    from solution import is_palindrome\n"
            "    assert is_palindrome('racecar') is True\n"
            "    assert is_palindrome('A man a plan a canal Panama') is True\n"
            "    assert is_palindrome('hello') is False\n"
            "    assert is_palindrome('') is True"
        ),
        expected_patterns=["def is_palindrome", "lower", "replace", "=="],
        allowed_subnets=["sn4"],
        available_tools=TOOLS_SN4,
        max_budget=0.015,
        max_latency=10,
    ),
    code_task(
        task_id="code_004",
        description="Implement a stack class with push, pop, peek, and is_empty methods.",
        test_suite=(
            "def test_stack():\n"
            "    from solution import Stack\n"
            "    s = Stack()\n"
            "    assert s.is_empty() is True\n"
            "    s.push(10)\n"
            "    s.push(20)\n"
            "    assert s.peek() == 20\n"
            "    assert s.pop() == 20\n"
            "    assert s.pop() == 10\n"
            "    assert s.is_empty() is True"
        ),
        expected_patterns=["class Stack", "def push", "def pop", "def peek", "def is_empty"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.025,
        max_latency=15,
    ),
    code_task(
        task_id="code_005",
        description="Implement a function that returns the longest common prefix of a list of strings.",
        test_suite=(
            "def test_lcp():\n"
            "    from solution import longest_common_prefix\n"
            "    assert longest_common_prefix(['flower','flow','flight']) == 'fl'\n"
            "    assert longest_common_prefix(['dog','racecar','car']) == ''\n"
            "    assert longest_common_prefix(['same','same','same']) == 'same'\n"
            "    assert longest_common_prefix([]) == ''"
        ),
        expected_patterns=["def longest_common_prefix", "zip", "prefix"],
        allowed_subnets=["sn4"],
        available_tools=TOOLS_SN4,
        max_budget=0.018,
        max_latency=12,
    ),
    code_task(
        task_id="code_006",
        description="Implement a function that flattens a nested list of arbitrary depth into a single list.",
        test_suite=(
            "def test_flatten():\n"
            "    from solution import flatten\n"
            "    assert flatten([1,[2,[3,[4]]]]) == [1,2,3,4]\n"
            "    assert flatten([]) == []\n"
            "    assert flatten([1,2,3]) == [1,2,3]\n"
            "    assert flatten([[1,2],[3,[4,5]]]) == [1,2,3,4,5]"
        ),
        expected_patterns=["def flatten", "isinstance", "list", "extend"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.02,
        max_latency=12,
    ),
    code_task(
        task_id="code_007",
        description="Implement a function that groups a list of words by their anagram equivalence class.",
        test_suite=(
            "def test_group_anagrams():\n"
            "    from solution import group_anagrams\n"
            "    result = group_anagrams(['eat','tea','tan','ate','nat','bat'])\n"
            "    assert len(result) == 3\n"
            "    assert sorted(['eat','tea','ate']) in [sorted(g) for g in result]\n"
            "    assert group_anagrams([]) == []"
        ),
        expected_patterns=["def group_anagrams", "sorted", "dict", "defaultdict"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.025,
        max_latency=15,
    ),
    code_task(
        task_id="code_008",
        description="Implement a function to compute the GCD of two positive integers using the Euclidean algorithm.",
        test_suite=(
            "def test_gcd():\n"
            "    from solution import gcd\n"
            "    assert gcd(48, 18) == 6\n"
            "    assert gcd(100, 25) == 25\n"
            "    assert gcd(1, 1) == 1\n"
            "    assert gcd(7, 13) == 1"
        ),
        expected_patterns=["def gcd", "while", "%" , "remainder"],
        allowed_subnets=["sn4"],
        available_tools=TOOLS_SN4,
        max_budget=0.012,
        max_latency=8,
    ),
    code_task(
        task_id="code_009",
        description="Implement a function that converts a Roman numeral string to an integer.",
        test_suite=(
            "def test_roman_to_int():\n"
            "    from solution import roman_to_int\n"
            "    assert roman_to_int('III') == 3\n"
            "    assert roman_to_int('IV') == 4\n"
            "    assert roman_to_int('IX') == 9\n"
            "    assert roman_to_int('LVIII') == 58\n"
            "    assert roman_to_int('MCMXCIV') == 1994"
        ),
        expected_patterns=["def roman_to_int", "dict", "I", "V", "X", "L"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.022,
        max_latency=14,
    ),
    code_task(
        task_id="code_010",
        description="Implement a queue using two stacks. Support enqueue and dequeue operations in amortized O(1).",
        test_suite=(
            "def test_queue_from_stacks():\n"
            "    from solution import QueueFromStacks\n"
            "    q = QueueFromStacks()\n"
            "    q.enqueue(1)\n"
            "    q.enqueue(2)\n"
            "    q.enqueue(3)\n"
            "    assert q.dequeue() == 1\n"
            "    assert q.dequeue() == 2\n"
            "    q.enqueue(4)\n"
            "    assert q.dequeue() == 3\n"
            "    assert q.dequeue() == 4"
        ),
        expected_patterns=["class QueueFromStacks", "def enqueue", "def dequeue", "stack"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.03,
        max_latency=18,
    ),
    code_task(
        task_id="code_011",
        description="Implement a function that given an array of integers returns all unique triplets that sum to zero.",
        test_suite=(
            "def test_three_sum():\n"
            "    from solution import three_sum\n"
            "    result = three_sum([-1,0,1,2,-1,-4])\n"
            "    assert sorted([sorted(t) for t in result]) == [[-1,-1,2],[-1,0,1]]\n"
            "    assert three_sum([]) == []\n"
            "    assert three_sum([0,0,0]) == [[0,0,0]]"
        ),
        expected_patterns=["def three_sum", "sort", "two pointer", "set"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.025,
        max_latency=15,
    ),
    code_task(
        task_id="code_012",
        description="Implement a min-heap data structure with insert and extract_min operations.",
        test_suite=(
            "def test_min_heap():\n"
            "    from solution import MinHeap\n"
            "    h = MinHeap()\n"
            "    for v in [5, 3, 8, 1, 4]:\n"
            "        h.insert(v)\n"
            "    assert h.extract_min() == 1\n"
            "    assert h.extract_min() == 3\n"
            "    assert h.extract_min() == 4"
        ),
        expected_patterns=["class MinHeap", "def insert", "def extract_min", "_heapify"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.03,
        max_latency=18,
    ),
    code_task(
        task_id="code_013",
        description="Implement a function that validates a Sudoku board (9x9 grid). Partial boards are valid if no row, column, or 3x3 box contains duplicate digits 1–9.",
        test_suite=(
            "def test_valid_sudoku():\n"
            "    from solution import is_valid_sudoku\n"
            "    board = [\n"
            "        ['5','3','.','.','7','.','.','.','.'],\n"
            "        ['6','.','.','1','9','5','.','.','.'],\n"
            "        ['.','9','8','.','.','.','.','6','.'],\n"
            "        ['8','.','.','.','6','.','.','.','3'],\n"
            "        ['4','.','.','8','.','3','.','.','1'],\n"
            "        ['7','.','.','.','2','.','.','.','6'],\n"
            "        ['.','6','.','.','.','.','2','8','.'],\n"
            "        ['.','.','.','4','1','9','.','.','5'],\n"
            "        ['.','.','.','.','8','.','.','7','9'],\n"
            "    ]\n"
            "    assert is_valid_sudoku(board) is True"
        ),
        expected_patterns=["def is_valid_sudoku", "set", "row", "col", "box"],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.025,
        max_latency=15,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# RAG TASKS  (12 total)
# ═════════════════════════════════════════════════════════════════════════════

RAG_TASKS = [
    rag_task(
        task_id="rag_001",
        description="What is Bittensor's consensus mechanism and how does Yuma Consensus differ from standard Proof-of-Work?",
        reference_answer=(
            "Bittensor uses Yuma Consensus, a stake-weighted agreement mechanism where validators assign scores to miners based on the quality of their outputs. "
            "Unlike Proof-of-Work, which requires energy-intensive computation to solve arbitrary puzzles, Yuma Consensus rewards useful machine-learning or computational work "
            "evaluated by validator peers who hold stake in the network."
        ),
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_002",
        description="Explain the role of subnets in the Bittensor ecosystem and how incentives flow between subnet owners, validators, and miners.",
        reference_answer=(
            "Subnets are specialized sub-networks within Bittensor, each defining its own task domain and scoring rules. "
            "Subnet owners set hyperparameters and emit Alpha tokens; validators query miners and set weights based on performance; "
            "miners compete to produce the best outputs and earn emissions proportional to their weight in the subnet."
        ),
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_003",
        description="What is a DAG (Directed Acyclic Graph) and how is it used to represent computational workflows?",
        reference_answer=(
            "A DAG is a graph with directed edges and no cycles, making it ideal for representing ordered computations where each node depends on its predecessors. "
            "In workflow orchestration, each DAG node represents a task or service call, and edges encode data flow and execution dependencies. "
            "This structure enables parallel execution of independent branches and clear dependency tracking."
        ),
        allowed_subnets=["sn1", "sn18"],
        available_tools=TOOLS_SN1_SN18,
        max_budget=0.008,
        max_latency=8,
    ),
    rag_task(
        task_id="rag_004",
        description="Describe the transformer architecture and explain the role of self-attention in language models.",
        reference_answer=(
            "The transformer is a neural network architecture that processes sequences in parallel using attention mechanisms rather than recurrence. "
            "Self-attention allows each token to attend to every other token in the sequence, computing weighted sums of value vectors guided by query-key similarity. "
            "This enables the model to capture long-range dependencies efficiently and is the foundation of modern large language models."
        ),
        allowed_subnets=["sn1", "sn18"],
        available_tools=TOOLS_SN1_SN18,
        max_budget=0.012,
        max_latency=12,
    ),
    rag_task(
        task_id="rag_005",
        description="What is retrieval-augmented generation (RAG) and how does it improve language model outputs?",
        reference_answer=(
            "Retrieval-augmented generation combines a retrieval system with a generative language model: at inference time, relevant documents are fetched from an external corpus "
            "and provided as context alongside the user query. This grounding reduces hallucination, keeps knowledge up-to-date without retraining, "
            "and allows the model to cite sources, significantly improving factual accuracy on knowledge-intensive tasks."
        ),
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.015,
        max_latency=15,
    ),
    rag_task(
        task_id="rag_006",
        description="Explain how Byzantine fault tolerance works in distributed systems and why it matters for blockchain networks.",
        reference_answer=(
            "Byzantine fault tolerance (BFT) allows a distributed system to reach consensus even when some nodes behave arbitrarily or maliciously. "
            "Classic BFT protocols tolerate up to one-third of nodes being Byzantine. In blockchain networks, BFT-inspired mechanisms prevent double-spending and ensure "
            "that all honest participants agree on the canonical chain state, which is critical for financial integrity and trustlessness."
        ),
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_007",
        description="What is gradient descent and how do adaptive optimizers like Adam improve upon vanilla SGD?",
        reference_answer=(
            "Gradient descent updates model parameters by stepping in the direction of the negative gradient of the loss function. "
            "Vanilla SGD uses a fixed learning rate, which can lead to slow convergence or oscillation. "
            "Adam combines momentum (first moment) with adaptive per-parameter learning rates (second moment), allowing faster convergence and better handling of sparse gradients."
        ),
        allowed_subnets=["sn1", "sn18"],
        available_tools=TOOLS_SN1_SN18,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_008",
        description="Describe the CAP theorem and its implications for distributed database design.",
        reference_answer=(
            "The CAP theorem states that a distributed system can simultaneously guarantee at most two of: Consistency, Availability, and Partition tolerance. "
            "Since network partitions are unavoidable in practice, designers must choose between strong consistency (sacrificing availability during partitions) "
            "or high availability (allowing stale reads during partitions). This trade-off shapes the design of systems like Cassandra (AP) versus HBase (CP)."
        ),
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_009",
        description="What are zero-knowledge proofs and how can they be used to enhance privacy in blockchain transactions?",
        reference_answer=(
            "Zero-knowledge proofs allow a prover to convince a verifier that a statement is true without revealing any information beyond the truth of the statement. "
            "In blockchains, ZK proofs enable private transactions: a user can prove they have sufficient funds or valid credentials without exposing balances or identity. "
            "ZK-SNARKs and ZK-STARKs are practical constructions used in systems like Zcash and StarkNet."
        ),
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.012,
        max_latency=12,
    ),
    rag_task(
        task_id="rag_010",
        description="Explain the difference between vertical and horizontal scaling in cloud infrastructure.",
        reference_answer=(
            "Vertical scaling (scale-up) means increasing the resources of a single server, such as adding more CPU cores or RAM. "
            "Horizontal scaling (scale-out) means adding more servers and distributing the load across them. "
            "Horizontal scaling is generally more fault-tolerant and cost-effective at large scale but requires stateless application design and a load balancer; "
            "vertical scaling is simpler but has hardware limits and creates a single point of failure."
        ),
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.008,
        max_latency=8,
    ),
    rag_task(
        task_id="rag_011",
        description="What is federated learning and how does it protect user data privacy while training machine learning models?",
        reference_answer=(
            "Federated learning trains a shared model across many devices without centralizing raw data. "
            "Each device trains locally on its own data and sends only model updates (gradients or weights) to a central aggregator. "
            "This keeps personal data on-device, reducing privacy risk. Techniques like differential privacy and secure aggregation further prevent the aggregator from inferring individual contributions."
        ),
        allowed_subnets=["sn1", "sn18"],
        available_tools=TOOLS_SN1_SN18,
        max_budget=0.01,
        max_latency=10,
    ),
    rag_task(
        task_id="rag_012",
        description="Describe how IPFS (InterPlanetary File System) stores and retrieves content, and how it differs from traditional HTTP.",
        reference_answer=(
            "IPFS uses content-addressed storage: files are identified by their cryptographic hash (CID) rather than by location. "
            "When you request a CID, IPFS retrieves it from any peer that has it, enabling decentralized, resilient storage. "
            "In contrast, HTTP retrieves files from a specific server URL; if that server goes down, the content becomes unavailable. "
            "IPFS also deduplicates identical content and makes data persist as long as at least one node pins it."
        ),
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.01,
        max_latency=10,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# AGENT TASKS  (13 total)
# ═════════════════════════════════════════════════════════════════════════════

AGENT_TASKS = [
    agent_task(
        task_id="agent_001",
        description="Calculate the compound interest on a principal of $5,000 at 6% annual rate compounded quarterly for 3 years. Report the final amount.",
        goal_checklist=[
            {"type": "regex", "pattern": r"5955\.\d+|5956\.\d+"},
            {"type": "keyword", "value": "compound"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    agent_task(
        task_id="agent_002",
        description="Identify the three largest countries by land area and list them in descending order with their approximate areas in km².",
        goal_checklist=[
            {"type": "keyword", "value": "Russia"},
            {"type": "keyword", "value": "Canada"},
            {"type": "keyword", "value": "United States"},
            {"type": "regex", "pattern": r"17[,\s]?\d{3}"},
        ],
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.015,
        max_latency=20,
    ),
    agent_task(
        task_id="agent_003",
        description="Convert the temperature 37.5°C to both Fahrenheit and Kelvin. Provide both results.",
        goal_checklist=[
            {"type": "regex", "pattern": r"99\.5"},
            {"type": "regex", "pattern": r"310\.6|310\.65"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.008,
        max_latency=8,
    ),
    agent_task(
        task_id="agent_004",
        description="Given the sequence 2, 6, 18, 54, …, identify the pattern and compute the 8th term.",
        goal_checklist=[
            {"type": "regex", "pattern": r"4374"},
            {"type": "keyword", "value": "geometric"},
            {"type": "regex", "pattern": r"ratio.*3|3.*ratio|multiply.*3|3.*multiply"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    agent_task(
        task_id="agent_005",
        description="Summarize the key steps to deploy a containerized Python web application on Kubernetes, covering at minimum: Docker image build, push, Deployment manifest, and Service manifest.",
        goal_checklist=[
            {"type": "keyword", "value": "docker build"},
            {"type": "keyword", "value": "docker push"},
            {"type": "keyword", "value": "Deployment"},
            {"type": "keyword", "value": "Service"},
            {"type": "keyword", "value": "kubectl apply"},
        ],
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.015,
        max_latency=20,
    ),
    agent_task(
        task_id="agent_006",
        description="Calculate the SHA-256 hash of the string 'bittensor' and report the first 16 hex characters.",
        goal_checklist=[
            {"type": "regex", "pattern": r"[0-9a-f]{16}"},
            {"type": "keyword", "value": "sha"},
        ],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.012,
        max_latency=12,
    ),
    agent_task(
        task_id="agent_007",
        description="List the prime numbers between 50 and 100, then compute their sum.",
        goal_checklist=[
            {"type": "keyword", "value": "53"},
            {"type": "keyword", "value": "59"},
            {"type": "keyword", "value": "61"},
            {"type": "keyword", "value": "67"},
            {"type": "keyword", "value": "71"},
            {"type": "keyword", "value": "73"},
            {"type": "keyword", "value": "79"},
            {"type": "keyword", "value": "83"},
            {"type": "keyword", "value": "89"},
            {"type": "keyword", "value": "97"},
            {"type": "regex", "pattern": r"712"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    agent_task(
        task_id="agent_008",
        description="Describe the steps required to implement OAuth2 authorization code flow for a web application, including redirect URI handling and token exchange.",
        goal_checklist=[
            {"type": "keyword", "value": "authorization code"},
            {"type": "keyword", "value": "redirect"},
            {"type": "keyword", "value": "access token"},
            {"type": "keyword", "value": "client secret"},
            {"type": "keyword", "value": "scope"},
        ],
        allowed_subnets=["sn1", "sn22"],
        available_tools=TOOLS_SN1_SN22,
        max_budget=0.015,
        max_latency=18,
    ),
    agent_task(
        task_id="agent_009",
        description="Solve the system of linear equations: 3x + 2y = 12, x - y = 1. Report the values of x and y.",
        goal_checklist=[
            {"type": "regex", "pattern": r"x\s*=\s*2|x\s*=\s*14/5"},
            {"type": "regex", "pattern": r"y\s*=\s*3|y\s*=\s*9/5"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.008,
        max_latency=8,
    ),
    agent_task(
        task_id="agent_010",
        description="Outline the key differences between REST and GraphQL APIs, covering response shape, over-fetching, and tooling.",
        goal_checklist=[
            {"type": "keyword", "value": "REST"},
            {"type": "keyword", "value": "GraphQL"},
            {"type": "keyword", "value": "over-fetching"},
            {"type": "keyword", "value": "schema"},
            {"type": "keyword", "value": "query"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=12,
    ),
    agent_task(
        task_id="agent_011",
        description="Compute the determinant of the 3x3 matrix [[2,1,3],[0,4,1],[5,2,0]] and report the result.",
        goal_checklist=[
            {"type": "regex", "pattern": r"-\s*39|-39"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.01,
        max_latency=10,
    ),
    agent_task(
        task_id="agent_012",
        description="Describe how to set up a Python virtual environment, install dependencies from requirements.txt, and run a pytest test suite.",
        goal_checklist=[
            {"type": "keyword", "value": "python -m venv"},
            {"type": "keyword", "value": "activate"},
            {"type": "keyword", "value": "pip install"},
            {"type": "keyword", "value": "requirements.txt"},
            {"type": "keyword", "value": "pytest"},
        ],
        allowed_subnets=["sn1", "sn4"],
        available_tools=TOOLS_SN1_SN4,
        max_budget=0.012,
        max_latency=12,
    ),
    agent_task(
        task_id="agent_013",
        description="Find the area under the curve f(x) = x² from x=0 to x=3 using integration, and verify using the trapezoidal rule with n=6 intervals.",
        goal_checklist=[
            {"type": "regex", "pattern": r"9\.0|9\.00"},
            {"type": "keyword", "value": "trapezoidal"},
            {"type": "regex", "pattern": r"antiderivative|x\^3|x³"},
        ],
        allowed_subnets=["sn1"],
        available_tools=TOOLS_SN1,
        max_budget=0.012,
        max_latency=12,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# DATA TRANSFORM TASKS  (12 total)
# ═════════════════════════════════════════════════════════════════════════════

DATA_TASKS = [
    data_task(
        task_id="data_001",
        description="Convert this CSV row to JSON: name,age,city\nAlice,30,Delhi",
        expected_output='{"name": "Alice", "age": "30", "city": "Delhi"}',
        allowed_subnets=["sn1", "sn13"],
        available_tools=TOOLS_SN1_SN13,
        max_budget=0.005,
        max_latency=8,
    ),
    data_task(
        task_id="data_002",
        description="Sort the following list of integers in ascending order and return as a comma-separated string: [42, 7, 19, 3, 88, 1]",
        expected_output="1,3,7,19,42,88",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.004,
        max_latency=6,
    ),
    data_task(
        task_id="data_003",
        description="Extract all email addresses from the following text and return them as a JSON array: 'Contact us at support@example.com or sales@acme.org for help.'",
        expected_output='["support@example.com", "sales@acme.org"]',
        allowed_subnets=["sn1", "sn13"],
        available_tools=TOOLS_SN1_SN13,
        max_budget=0.006,
        max_latency=8,
    ),
    data_task(
        task_id="data_004",
        description="Compute the word frequency map for the string 'the cat sat on the mat the cat' and return as JSON sorted by key.",
        expected_output='{"cat": 2, "mat": 1, "on": 1, "sat": 1, "the": 3}',
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.005,
        max_latency=7,
    ),
    data_task(
        task_id="data_005",
        description="Flatten and deduplicate the nested list [[1,2,3],[2,3,4],[4,5]] into a sorted unique list, returning as a JSON array.",
        expected_output="[1, 2, 3, 4, 5]",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.004,
        max_latency=6,
    ),
    data_task(
        task_id="data_006",
        description="Convert the following XML to JSON: <person><name>Bob</name><age>25</age></person>",
        expected_output='{"person": {"name": "Bob", "age": "25"}}',
        allowed_subnets=["sn1", "sn13"],
        available_tools=TOOLS_SN1_SN13,
        max_budget=0.006,
        max_latency=8,
    ),
    data_task(
        task_id="data_007",
        description="Given the JSON array [{\"score\": 80}, {\"score\": 95}, {\"score\": 70}], compute the average score and return as a float with 2 decimal places.",
        expected_output="81.67",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.004,
        max_latency=6,
    ),
    data_task(
        task_id="data_008",
        description="Normalize the string 'Hello,  World!  This  is   a   test.' by collapsing multiple spaces to a single space and trimming leading/trailing whitespace.",
        expected_output="Hello, World! This is a test.",
        allowed_subnets=["sn1", "sn13"],
        available_tools=TOOLS_SN1_SN13,
        max_budget=0.004,
        max_latency=6,
    ),
    data_task(
        task_id="data_009",
        description="Convert this JSON to a pipe-delimited table (header + 1 row): [{\"id\": 1, \"product\": \"Widget\", \"price\": 9.99}]",
        expected_output="id|product|price\n1|Widget|9.99",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.005,
        max_latency=7,
    ),
    data_task(
        task_id="data_010",
        description="Given the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3], return the top-3 most frequent elements as a JSON array sorted by frequency descending then value ascending.",
        expected_output="[1, 3, 5]",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.005,
        max_latency=7,
    ),
    data_task(
        task_id="data_011",
        description="Decode the Base64 string 'SGVsbG8sIFdvcmxkIQ==' and return the plaintext.",
        expected_output="Hello, World!",
        allowed_subnets=["sn1", "sn13"],
        available_tools=TOOLS_SN1_SN13,
        max_budget=0.003,
        max_latency=5,
    ),
    data_task(
        task_id="data_012",
        description="Given the camelCase string 'getUserProfileDataByEmail', convert it to snake_case.",
        expected_output="get_user_profile_data_by_email",
        allowed_subnets=["sn13"],
        available_tools=TOOLS_SN13,
        max_budget=0.003,
        max_latency=5,
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
# SYNTHETIC TASKS  (10 total, ~17% of 60)
# ═════════════════════════════════════════════════════════════════════════════
# Synthetic tasks are variants of base tasks with type="synthetic" and
# optionally an optimal_workflow reference.

SYNTHETIC_TASKS = [
    # Variant of code_001 — use itertools approach
    {
        **CODE_TASKS[0],
        "task_id": "synthetic_001",
        "type": "synthetic",
        "description": "Implement a Python function that merges two sorted lists into one sorted list using a generator-based approach.",
        "reference": {
            **CODE_TASKS[0]["reference"],
            "optimal_workflow": workflow(
                ("step_1", "sn4", "generate_code"),
                ("step_2", "sn4", "generate_tests"),
            ),
        },
    },
    # Variant of code_002 — recursive binary search
    {
        **CODE_TASKS[1],
        "task_id": "synthetic_002",
        "type": "synthetic",
        "description": "Implement a recursive binary search function that returns the index of a target in a sorted list, or -1 if not found.",
        "reference": {
            **CODE_TASKS[1]["reference"],
            "optimal_workflow": workflow(
                ("step_1", "sn4", "generate_code"),
                ("step_2", "sn1", "review_code"),
            ),
        },
    },
    # Variant of rag_003 — focus on topological sort
    {
        **RAG_TASKS[2],
        "task_id": "synthetic_003",
        "type": "synthetic",
        "description": "What is topological sort and how is it applied to schedule tasks in a DAG-based workflow engine?",
        "reference": {
            "reference_answer": (
                "Topological sort produces a linear ordering of DAG nodes such that every node appears before all nodes it has an edge to. "
                "In workflow engines, topological sort determines the safe execution order of tasks respecting all data dependencies. "
                "It is computed via DFS post-order or Kahn's algorithm and detects cycles that would make scheduling impossible."
            ),
            "optimal_workflow": workflow(
                ("step_1", "sn1", "retrieve_context"),
                ("step_2", "sn1", "generate_answer"),
            ),
        },
    },
    # Variant of agent_001 — different principal/rate
    {
        **AGENT_TASKS[0],
        "task_id": "synthetic_004",
        "type": "synthetic",
        "description": "Calculate the compound interest on a principal of $10,000 at 4% annual rate compounded monthly for 2 years. Report the final amount.",
        "reference": {
            "goal_checklist": [
                {"type": "regex", "pattern": r"10832\.\d+|10833\.\d+"},
                {"type": "keyword", "value": "compound"},
            ],
            "optimal_workflow": workflow(
                ("step_1", "sn1", "compute"),
                ("step_2", "sn1", "format_output"),
            ),
        },
    },
    # Variant of data_001 — different CSV
    {
        **DATA_TASKS[0],
        "task_id": "synthetic_005",
        "type": "synthetic",
        "description": "Convert this CSV row to JSON: id,username,email\n42,jdoe,jdoe@example.com",
        "reference": {
            "expected_output": '{"id": "42", "username": "jdoe", "email": "jdoe@example.com"}',
            "optimal_workflow": workflow(
                ("step_1", "sn13", "parse_csv"),
                ("step_2", "sn13", "serialize_json"),
            ),
        },
    },
    # Variant of code_006 — iterative flatten
    {
        **CODE_TASKS[5],
        "task_id": "synthetic_006",
        "type": "synthetic",
        "description": "Implement an iterative (non-recursive) function that flattens a nested list of arbitrary depth into a single list.",
        "reference": {
            **CODE_TASKS[5]["reference"],
            "optimal_workflow": workflow(
                ("step_1", "sn4", "generate_code"),
                ("step_2", "sn1", "review_logic"),
                ("step_3", "sn4", "generate_tests"),
            ),
        },
    },
    # Variant of rag_005 — focus on vector databases in RAG
    {
        **RAG_TASKS[4],
        "task_id": "synthetic_007",
        "type": "synthetic",
        "description": "How do vector databases enable semantic search in RAG systems, and what embedding models are commonly used?",
        "reference": {
            "reference_answer": (
                "Vector databases store high-dimensional embedding vectors and support approximate nearest-neighbour search. "
                "In RAG pipelines, documents are encoded into vectors at index time and queries are encoded at retrieval time; "
                "the most semantically similar document embeddings are returned as context. "
                "Common embedding models include OpenAI Ada, Sentence-BERT, and E5-large."
            ),
            "optimal_workflow": workflow(
                ("step_1", "sn22", "fetch_docs"),
                ("step_1b", "sn18", "embed"),
                ("step_2", "sn1", "generate_answer"),
            ),
        },
    },
    # Variant of agent_007 — primes between 100 and 150
    {
        **AGENT_TASKS[6],
        "task_id": "synthetic_008",
        "type": "synthetic",
        "description": "List the prime numbers between 100 and 150, then compute their sum.",
        "reference": {
            "goal_checklist": [
                {"type": "keyword", "value": "101"},
                {"type": "keyword", "value": "103"},
                {"type": "keyword", "value": "107"},
                {"type": "keyword", "value": "109"},
                {"type": "keyword", "value": "113"},
                {"type": "keyword", "value": "127"},
                {"type": "keyword", "value": "131"},
                {"type": "keyword", "value": "137"},
                {"type": "keyword", "value": "139"},
                {"type": "keyword", "value": "149"},
                {"type": "regex", "pattern": r"1216"},
            ],
            "optimal_workflow": workflow(
                ("step_1", "sn1", "enumerate_primes"),
                ("step_2", "sn1", "sum_and_format"),
            ),
        },
    },
    # Variant of data_012 — PascalCase to snake_case
    {
        **DATA_TASKS[11],
        "task_id": "synthetic_009",
        "type": "synthetic",
        "description": "Given the PascalCase string 'UserProfileService', convert it to snake_case.",
        "reference": {
            "expected_output": "user_profile_service",
            "optimal_workflow": workflow(
                ("step_1", "sn13", "transform_case"),
            ),
        },
    },
    # Variant of code_003 — palindrome for numbers
    {
        **CODE_TASKS[2],
        "task_id": "synthetic_010",
        "type": "synthetic",
        "description": "Implement a function that checks whether a given integer is a palindrome (same forwards and backwards as a digit string).",
        "reference": {
            "test_suite": (
                "def test_numeric_palindrome():\n"
                "    from solution import is_numeric_palindrome\n"
                "    assert is_numeric_palindrome(121) is True\n"
                "    assert is_numeric_palindrome(-121) is False\n"
                "    assert is_numeric_palindrome(10) is False\n"
                "    assert is_numeric_palindrome(0) is True"
            ),
            "expected_patterns": ["def is_numeric_palindrome", "str", "=="],
            "optimal_workflow": workflow(
                ("step_1", "sn4", "generate_code"),
                ("step_2", "sn4", "test_code"),
            ),
        },
    },
]


# ═════════════════════════════════════════════════════════════════════════════
# Assemble and validate
# ═════════════════════════════════════════════════════════════════════════════

def build_benchmark():
    tasks = CODE_TASKS + RAG_TASKS + AGENT_TASKS + DATA_TASKS + SYNTHETIC_TASKS

    # Validate counts
    total = len(tasks)
    active = [t for t in tasks if t.get("status") == "active"]
    synthetic = [t for t in tasks if t.get("type") == "synthetic"]
    ratio = len(synthetic) / total

    assert total >= 60, f"Expected >= 60 tasks, got {total}"
    assert len(active) >= 50, f"Expected >= 50 active tasks, got {len(active)}"
    assert 0.15 <= ratio <= 0.20, (
        f"Synthetic ratio {ratio:.2%} outside 15-20% band "
        f"({len(synthetic)}/{total})"
    )

    # Validate all task IDs are unique
    ids = [t["task_id"] for t in tasks]
    assert len(ids) == len(set(ids)), f"Duplicate task_id found: {[i for i in ids if ids.count(i) > 1]}"

    # Validate required fields
    required_fields = {"task_id", "task_type", "status", "description",
                       "quality_criteria", "constraints", "available_tools",
                       "routing_policy", "reference"}
    for t in tasks:
        missing = required_fields - set(t.keys())
        assert not missing, f"Task {t.get('task_id')} missing fields: {missing}"

    # Print summary to stderr so stdout is clean JSON
    type_counts = {}
    for t in tasks:
        tt = t.get("task_type", "unknown")
        type_counts[tt] = type_counts.get(tt, 0) + 1

    print(
        f"[generate_benchmarks] {total} tasks | "
        f"active={len(active)} | "
        f"synthetic={len(synthetic)} ({ratio:.1%}) | "
        f"types={type_counts}",
        file=sys.stderr,
    )

    return tasks


if __name__ == "__main__":
    tasks = build_benchmark()
    print(json.dumps(tasks, indent=2))
