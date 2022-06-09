"""This module exposes PactClient class which is an entry points for interacting with the SDK.

Typical usage example::

    import algosdk
    from algosdk.v2client.algod import AlgodClient

    import pactsdk

    algod = AlgodClient("<token>", "<url>")
    pact = pactsdk.PactClient(algod)

    algo = pact.fetch_asset(0)
    other_coin = pact.fetch_asset(12345678)

    pools = pact.fetch_pools_by_assets(algo, other_coin)
"""
from typing import Union

from algosdk.v2client.algod import AlgodClient

from pactsdk.api import ApiListPoolsResponse

from .asset import Asset, fetch_asset_by_index
from .pool import (
    ListPoolsParams,
    Pool,
    fetch_pool_by_id,
    fetch_pools_by_assets,
    list_pools,
)


class PactClient:
    """An entry point for interacting with the SDK.

    Exposes convenience methods for fetching assets and pools.
    """

    algod: AlgodClient
    """Algorand client to work with."""

    pact_api_url: str
    """Pact API URL to use."""

    def __init__(self, algod: AlgodClient, pact_api_url: str = "https://api.pact.fi"):
        """Constructor for the PactClient class.

        Args:
            algod: Algorand client to work with.
            pact_api_url: Pact API URL to use.
        """
        self.algod = algod
        self.pact_api_url = pact_api_url

    def fetch_asset(self, asset_index: int) -> Asset:
        """A convenient method for fetching ASAs (Algorand Standard Asset).

        This will return an Asset class with the relevant data about the asset if the asset index is valid.
        Note that an index of zero (0) will return the Algo asset.

        Args:
            asset_index: The id of the asset.

        Raises:
            algosdk.error.AlgodHTTPError: If the asset does not exist.

        Returns:
            Asset instance for the given index.
        """
        return fetch_asset_by_index(self.algod, asset_index)

    def list_pools(self, params: ListPoolsParams = None) -> ApiListPoolsResponse:
        """Returns a list of pools according to the pool options passed in. Uses Pact API for fetching the data.

        Args:
            params: API call parameters.

        Returns:
            Paginated list of pools.
        """
        return list_pools(self.pact_api_url, params or {})

    def fetch_pools_by_assets(
        self, primary_asset: Union[Asset, int], secondary_asset: Union[Asset, int]
    ) -> list[Pool]:
        """Returns a list of liquidity pools on Pact that are across the primary and secondary assets.

        First, it uses Pact API retrieve app ids matching the provided assets and then uses algod client to fetch contracts data from the blockchain.

        Args:
            primary_asset: Primary asset or the asset id for the pool to find.
            secondary_asset: Secondary asset or the asset id for the pool to find.

        Returns:
            List of pools for the two assets, the list may be empty.
        """
        return fetch_pools_by_assets(
            algod=self.algod,
            asset_a=primary_asset,
            asset_b=secondary_asset,
            pact_api_url=self.pact_api_url,
        )

    def fetch_pool_by_id(self, app_id: int) -> Pool:
        """Fetches the pool by the application id. It uses algod client to fetch the data directly from the blockchain.

        Args:
            app_id: The application id of pool to return.

        Raises:
            algosdk.error.AlgodHTTPError: If the pool does not exist.

        Returns:
            The pool for the application id.
        """
        return fetch_pool_by_id(algod=self.algod, app_id=app_id)
