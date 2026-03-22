"""
Tests for C-SWON mock classes.
Updated to use WorkflowSynapse instead of PromptingSynapse.
"""

import pytest
import asyncio
import bittensor as bt
from cswon.mock import MockDendrite, MockMetagraph, MockSubtensor
from cswon.protocol import WorkflowSynapse, Dummy


@pytest.mark.parametrize("netuid", [1, 2, 3])
@pytest.mark.parametrize("n", [2, 4, 8, 16])
@pytest.mark.parametrize("wallet", [bt.MockWallet(), None])
def test_mock_subtensor(netuid, n, wallet):
    subtensor = MockSubtensor(netuid=netuid, n=n, wallet=wallet)
    neurons = subtensor.neurons(netuid=netuid)
    assert subtensor.subnet_exists(netuid)
    assert subtensor.network == "mock"
    assert len(neurons) == (n + 1 if wallet is not None else n)
    if wallet is not None:
        assert subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address
        )


@pytest.mark.parametrize("n", [16, 32])
def test_mock_metagraph(n):
    mock_subtensor = MockSubtensor(netuid=1, n=n)
    mock_metagraph = MockMetagraph(subtensor=mock_subtensor)
    axons = mock_metagraph.axons
    assert len(axons) == n
    for axon in axons:
        assert type(axon) == bt.AxonInfo
        assert axon.ip == "127.0.0.0"
        assert axon.port == 8091


def test_mock_dendrite_workflow_synapse():
    """Test that MockDendrite returns proper WorkflowSynapse responses."""
    mock_wallet = bt.MockWallet()
    mock_dendrite = MockDendrite(mock_wallet)
    n = 4
    mock_subtensor = MockSubtensor(netuid=1, n=n, wallet=mock_wallet)
    mock_metagraph = MockMetagraph(subtensor=mock_subtensor)
    axons = mock_metagraph.axons

    synapse = WorkflowSynapse(
        task_id="test-001",
        task_type="code_generation_pipeline",
        description="Generate a simple function",
        constraints={"max_budget_tao": 0.05},
        available_tools={"SN1": {"type": "text_generation"}, "SN62": {"type": "code_review"}},
    )

    async def run():
        return await mock_dendrite.forward(
            axons=axons,
            synapse=synapse,
            timeout=10.0,
            deserialize=False,
        )

    responses = asyncio.run(run())

    for resp in responses:
        assert isinstance(resp, WorkflowSynapse)
        if resp.dendrite and resp.dendrite.status_code == 200:
            assert resp.workflow_plan is not None
            assert resp.miner_uid is not None
            assert resp.scoring_version is not None
            assert resp.confidence is not None


def test_mock_dendrite_legacy_dummy():
    """Test backward compatibility with Dummy synapse."""
    mock_wallet = bt.MockWallet()
    mock_dendrite = MockDendrite(mock_wallet)
    mock_subtensor = MockSubtensor(netuid=1, n=4, wallet=mock_wallet)
    mock_metagraph = MockMetagraph(subtensor=mock_subtensor)
    axons = mock_metagraph.axons

    async def run():
        return await mock_dendrite.forward(
            axons=axons,
            synapse=Dummy(dummy_input=5),
            timeout=10.0,
            deserialize=False,
        )

    responses = asyncio.run(run())
    for resp in responses:
        if resp.dendrite and resp.dendrite.status_code == 200:
            assert resp.dummy_output == 10  # 5 * 2
