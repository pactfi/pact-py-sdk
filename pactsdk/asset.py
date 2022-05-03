""" Utility functions and class for dealing with Algorand Standard Assets.

    This module contains an Asset class which encapsulates the basic information about the Algorand Standard Asset.
    It also includes utility functions for opting in and querying account information related to the asset.
    A factory function allows you to fetch the information by index number.

    Typical usage example:
    ```
    import algosdk
    from algosdk.v2client.algod import AlgodClient

    import pactsdk

    algod = AlgodClient("<token>", "<url>")  # provide options

    algo = fetch_asset_by_index(algod, 0)

    print(f"Asset {algo.name} has {algo.ratio} base units to an {algo.unit_name}.")
    # OUTPUT Asset Algo has 1000000 base units to an ALGO.
    ```
"""
import copy
from dataclasses import dataclass
from typing import Optional

from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

ASSETS_CACHE: dict[int, "Asset"] = {}
"""Dictionary mapping the asset index number to the Asset class to speed up look up of the asset information."""


def fetch_asset_by_index(
    algod: AlgodClient,
    index: int,
) -> "Asset":
    """Fetches the Asset class for a given id from the Algod Client.

    Convenience function for returning the Asset data class for the index passed in.
    This function uses a global ASSETS_CACHE to ensure that only one call to the Algod Client
    is made per index asset. A side effect of calling the function is that a new entry is made
    in the ASSET_CACHE if there isn't an entry for the index.



    Args:
        algod: An Algorand Client that is the source of the asset information.
        index: An integer representing the Algorand Standard Asset.
    Returns:
        A new Asset object whose index is the value passed in and whose Asset
            values are set from the asset_info.
    """
    if index in ASSETS_CACHE:
        return copy.copy(ASSETS_CACHE[index])

    if index > 0:
        asset_info = algod.asset_info(index)
        params = asset_info["params"]
    else:
        params = {
            "name": "Algo",
            "unit-name": "ALGO",
            "decimals": 6,
        }

    asset = Asset(
        algod=algod,
        index=index,
        decimals=params["decimals"],
        name=params.get("name"),
        unit_name=params.get("unit-name"),
    )

    ASSETS_CACHE[index] = asset

    return asset


@dataclass
class Asset:
    """Describes the basic details and utility functions for an Algorand Standard Asset.

    Includes basic details about the asset like name and decimals as well utility functions
    around the algorand functionality.
    While this is a data class it is typically constructed from a PactClient function like fetch_asset
    or via a pool or swap member variable.


    """

    algod: AlgodClient
    """Algorand Client used to look up the assets."""
    index: int
    """The unique index for the asset."""
    decimals: int
    """The number of decimal places between the asset displayed price and the base units."""
    name: Optional[str] = None
    """The display name of the asset. Set to None if there is no display name."""
    unit_name: Optional[str] = None
    """The name of the unit value for the asset. Set to None if there is no unit display name."""

    @property
    def ratio(self):
        """Returns the ratio of base units to asset value"""
        return 10**self.decimals

    def prepare_opt_in_tx(self, address: str):
        """Generates an opt_in transaction for this asset.

        Args:
            address (str): The sender and receiver address for the transaction to opt in.

        Returns:
            A new Asset Transfer Transacion for this asset with
            the sender and receiver set to the argument passed in.
            All other arguments are the default.
        """
        return transaction.AssetTransferTxn(
            sender=address,
            receiver=address,
            amt=0,
            index=self.index,
            sp=self.algod.suggested_params(),
        )

    def is_opted_in(self, address: str) -> bool:
        """Checks if a given account has opted in to this asset.

        This function uses the fact that any asset that has opted in will have a
        valid amount in the account.

        Args:
            address: The account address to check if the asset has been opted in.

        Returns:
            True if the account has opted in to the asset, false otherwise.
        """
        holding = self.get_holding(address)
        return holding is not None

    def get_holding(self, address: str) -> Optional[int]:
        """Returns the current amount of the Asset being held in an account.

        Args:
            address: The amount of a particular asset that is being held in the account

        Returns:
            An integer with the amount of the asset held in the account.
            If there is no asset then a none is returned.
        """
        account_info = self.algod.account_info(address)
        for asset in account_info["assets"]:
            if asset["asset-id"] == self.index:
                return asset["amount"]
        return None

    def __eq__(self, other_asset: object) -> bool:
        """Return equal by comparing the assets index value."""
        if not isinstance(other_asset, Asset):
            return False
        return self.index == other_asset.index
