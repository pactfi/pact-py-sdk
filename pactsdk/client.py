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
from typing import Optional, Union, cast

from algosdk.v2client.algod import AlgodClient

from pactsdk.api import ApiListPoolsResponse
from pactsdk.farming.farming_client import PactFarmingClient

from .asset import Asset, fetch_asset_by_index
from .config import Config, Network, get_config
from .factories import ConstantProductFactory, get_pool_factory
from .folks_lending_pool import (
    FolksLendingPool,
    FolksLendingPoolAdapter,
    fetch_folks_lending_pool,
)
from .gas_station import get_gas_station, set_gas_station
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

    config: Config
    """Client configuration with global contracts ids etc."""

    farming: PactFarmingClient

    def __init__(self, algod: AlgodClient, network: Network = "mainnet", **kwargs):
        """Constructor for the PactClient class.

        Args:
            algod: Algorand client to work with.
            network: The Algorand network to use the client with. The configuration values depend on the chosen network.
            kwargs: Use it to overwrite configuration parameters.
        """
        self.algod = algod
        self.config = get_config(network, **kwargs)
        self.farming = PactFarmingClient(algod, self.config)

        try:
            get_gas_station()
        except AssertionError:
            set_gas_station(self.config.gas_station_id)

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

    def list_pools(
        self, params: Optional[ListPoolsParams] = None
    ) -> ApiListPoolsResponse:
        """Returns a list of pools according to the pool options passed in. Uses Pact API for fetching the data.

        This method is deprecated but is kept for backward compatibility. Pact is in the process of changing the way the pools are created. In the future, all pools will be created using a pool factory contract which allows for an on-chain discoverability of pools.

        Args:
            params: API call parameters.

        Returns:
            Paginated list of pools.
        """
        return list_pools(self.config.api_url, params or {})

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
            pact_api_url=self.config.api_url,
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

    def fetch_folks_lending_pool(self, app_id: int) -> FolksLendingPool:
        """Fetches Folks Finance lending pool that can be used in FolksLendingPoolAdapter which allows higher APR than a normal pool.
        See :py:mod:`pactsdk.folks_lending_pool` for details.

        Args:
            app_id: The application id of the Folks Finance pool. You can find the ids here - https://docs.folks.finance/developer/contracts

        Returns:
            The Folks Finance lending pool for the given application id.
        """
        return fetch_folks_lending_pool(self.algod, app_id)

    def get_folks_lending_pool_adapter(
        self,
        pact_pool: Pool,
        primary_lending_pool: FolksLendingPool,
        secondary_lending_pool: FolksLendingPool,
    ) -> FolksLendingPoolAdapter:
        """Creates the adapter object that allows composing Folks Finance lending pools with Pact pool, resulting in a higher APR.
        See :py:mod:`pactsdk.folks_lending_pool` for details.

        Args:
            pact_pool: The Pact pool between two fAssets tokens.
            primary_lending_pool: The Folks Finance pool for the primary fAsset.
            secondary_lending_pool: The Folks Finance pool for the secondary fAsset.

        Returns:
            The adapter object.
        """
        return FolksLendingPoolAdapter(
            algod=self.algod,
            app_id=self.config.folks_lending_pool_adapter_id,
            pact_pool=pact_pool,
            primary_lending_pool=primary_lending_pool,
            secondary_lending_pool=secondary_lending_pool,
        )

    def get_constant_product_pool_factory(self) -> ConstantProductFactory:
        """Gets the constant product pool factory according to the client's configuration."""
        factory = get_pool_factory(
            algod=self.algod, pool_type="CONSTANT_PRODUCT", config=self.config
        )
        return cast(ConstantProductFactory, factory)

    def get_nft_constant_product_pool_factory(self) -> ConstantProductFactory:
        """Gets the NFT constant product pool factory according to the client's configuration."""
        factory = get_pool_factory(
            algod=self.algod, pool_type="NFT_CONSTANT_PRODUCT", config=self.config
        )
        return cast(ConstantProductFactory, factory)
