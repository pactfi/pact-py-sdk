"""PactClient is a simple client to handle requests to the pact exchange.

    The module wraps the AlgodClient to allow you to query the pact exchange. Primarily it is used to get a list of
    pools, either by asset, by id or overall.

    Typical usage example:
    ``` 
    import algosdk
    from algosdk.v2client.algod import AlgodClient

    import pactsdk

    algod = AlgodClient("<token>", "<url>")  # provide options
    pact = pactsdk.PactClient(algod)

    algo = pact.fetch_asset(0) #return the algo asset

    ```


"""
from typing import Union

from algosdk.v2client.algod import AlgodClient

from .asset import Asset, fetch_asset_by_index
from .pool import Pool, fetch_pool_by_id, fetch_pools_by_assets, list_pools


class PactClient:
    """A client for accessing general data about the Pact exchange.

    Attributes:
        algod (AlgodClient): AlgodClient for requests to algorand.
        pact_api_url (str): uri for the network to attach to.
    """

    def __init__(self, algod: AlgodClient, pact_api_url="https://api.pact.fi"):
        """Initialize the class to the values.

        Args:
            algod (AlgodClient): The sdk client for handling algorand requests.
            pact_api_url (str, optional): uri for the network to attach to. Defaults to "https://api.pact.fi".
        """
        self.algod = algod
        self.pact_api_url = pact_api_url

    def fetch_asset(self, asset_index: int) -> Asset:
        """Fetch the `pactsdk.asset.Asset` utility class for the given index number.

        This will return an Asset class with the relevant data about the asset if the asset index is valid.
        Note that an index of zero (0) will return the Algo asset.

        Args:
            asset_index (int): The index number for the asset that you want the data about.

        Returns:
            `Asset`: an `pactsdk.asset.Asset` class with the details about the asset for the given asset.
        """
        return fetch_asset_by_index(self.algod, asset_index)

    def list_pools(self, **kwargs) -> dict:
        """Lists all the pools currently available in the pact exchange.

        Returns:
            dict: returns a list of all pools in the exchange.
        """
        return list_pools(self.pact_api_url, **kwargs)

    def fetch_pools_by_assets(
        self, primary_asset: Union[Asset, int], secondary_asset: Union[Asset, int]
    ) -> list[Pool]:
        """Returns a list of the liquidity pools between the two assets passed in.

        Assets can be sent in as either the index or Asset data class.

        Args:
            primary_asset (Union[Asset, int]): Primary asset of the liquidity pool to return.
            secondary_asset (Union[Asset, int]): Secondary asset of the liquidity pool to return.

        Returns:
            list[Pool]: A list of pools that meet are between the two assets. List will be empty if there are no pools.
        """
        return fetch_pools_by_assets(
            algod=self.algod,
            asset_a=primary_asset,
            asset_b=secondary_asset,
            pact_api_url=self.pact_api_url,
        )

    def fetch_pool_by_id(self, app_id: int) -> Pool:
        """Returns the pool data for the id.

        Args:
            app_id (int): Unique identifier for the pool.

        Returns:
            Pool: Class representing the pool data.
        """
        return fetch_pool_by_id(algod=self.algod, app_id=app_id)
