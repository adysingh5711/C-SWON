import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cswon.base.neuron import BaseNeuron
from cswon.base.validator import BaseValidatorNeuron


class _DummyNeuron(BaseNeuron):
    async def forward(self, synapse):
        return synapse

    def run(self):
        return None


class _DummyValidator(BaseValidatorNeuron):
    async def forward(self):
        return None


class TestRuntimeRegressions(unittest.TestCase):
    def test_block_property_uses_subtensor(self):
        neuron = _DummyNeuron.__new__(_DummyNeuron)
        neuron.subtensor = object()

        with patch("cswon.base.neuron.ttl_get_block", return_value=12345) as mocked:
            self.assertEqual(neuron.block, 12345)
            mocked.assert_called_once_with(neuron.subtensor)

    def test_validator_serve_axon_starts_listener(self):
        validator = _DummyValidator.__new__(_DummyValidator)
        validator.wallet = SimpleNamespace(
            hotkey=SimpleNamespace(ss58_address="hotkey"),
            coldkeypub=SimpleNamespace(ss58_address="coldkey"),
        )
        validator.config = SimpleNamespace(
            subtensor=SimpleNamespace(network="test", chain_endpoint="ws://127.0.0.1:9944"),
            netuid=2,
        )
        validator.subtensor = SimpleNamespace(
            serve_axon=MagicMock(return_value=SimpleNamespace(success=True, message="")),
        )

        fake_axon = MagicMock()
        fake_axon.external_ip = "127.0.0.1"
        fake_axon.port = 8111
        fake_axon.external_port = 8111
        fake_axon.info = SimpleNamespace(description=None)

        with patch("cswon.base.validator.bt.Axon", return_value=fake_axon), patch(
            "cswon.base.validator.bt.AxonInfo", return_value=object()
        ), patch(
            "cswon.base.validator.serve_axon_via_btcli", return_value=(True, "")
        ):
            validator.serve_axon()

        fake_axon.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
