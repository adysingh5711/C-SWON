import pytest
from cswon.api.get_query_axons import get_query_api_axons


@pytest.mark.anyio
async def test_get_query_api_axons_requires_metagraph():
    """Passing metagraph=None must raise ValueError, not fallback to netuid=21."""
    with pytest.raises(ValueError, match="metagraph must be provided"):
        await get_query_api_axons(wallet=None, metagraph=None)
