"""Utility functions and class for dealing with Algorand Standard Assets."""

import copy
from dataclasses import dataclass
from typing import Optional

from algosdk import transaction
from algosdk.v2client.algod import AlgodClient

ASSETS_CACHE: dict[tuple[AlgodClient, int], "Asset"] = {}
"""Dictionary mapping the asset index number to the :py:class:`pactsdk.asset.Asset` class to speed up look up of the asset information."""


def get_cached_asset(algod: AlgodClient, index: int, decimals: int) -> "Asset":
    cache_key = (algod, index)
    if cache_key in ASSETS_CACHE:
        return copy.copy(ASSETS_CACHE[cache_key])

    return Asset(algod=algod, index=index, decimals=decimals)


def fetch_asset_by_index(
    algod: AlgodClient,
    index: int,
) -> "Asset":
    """Fetches an :py:class:`pactsdk.asset.Asset` class with the details about the asset for a given id number.

    The function uses an internal cache so as to minimize the number of times the actual Algorand client is used to look up the asset. This function is used through out the pact sdk to query asset information.

    Args:
        algod: An Algorand client to query about the asset.
        index: An Algorand Asset number to look up.
    Returns:
        An asset instance for the index passed in.
    """
    cache_key = (algod, index)
    if cache_key in ASSETS_CACHE:
        return copy.copy(ASSETS_CACHE[cache_key])

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

    ASSETS_CACHE[cache_key] = asset

    return asset


@dataclass
class Asset:
    """Describes the basic data and the utility functions for an Algorand Standard Asset.

    Typically you don't create instances of this class manually. Use :py:meth:`pactsdk.client.PactClient.fetch_asset` instead. Also, when instantiating the pool e.g. by using :py:meth:`pactsdk.client.PactClient.fetch_pool_by_id` the missing pool assets are fetched automatically.
    """

    algod: AlgodClient
    """The Algorand sdk client to use for extracting asset details."""

    index: int
    """The ID of the asset."""

    decimals: int
    """The number of decimal places that the Asset supports."""

    name: Optional[str] = None
    """The name of the Asset if there is one. This may be None."""

    unit_name: Optional[str] = None
    """The name of a unit of the asset if there is one. This may be None."""

    @property
    def ratio(self) -> int:
        """The ratio between a base unit and the unit of the asset.

        This is used to convert between an integer and floating point representation of the asset without loss of precision.
        """
        return 10**self.decimals

    def prepare_opt_in_tx(self, address: str) -> transaction.AssetTransferTxn:
        """This creates a transaction that will allow the account to "opt in" to the asset.

        In Algorand, every account has to explicitly opt-in for an asset before receiving it.
        Needed if you want to receive an asset from a swap or to manage liquidity tokens.

        Args:
            address: Account to opt in to this asset.

        Returns:
            A ready to send transaction to opt-in into the ASA.
        """
        suggested_params = self.algod.suggested_params()
        return self.build_opt_in_tx(address, suggested_params)

    def build_opt_in_tx(
        self, address: str, suggested_params: transaction.SuggestedParams
    ) -> transaction.AssetTransferTxn:
        """Creates the actual transaction for the account to opt-in to holding the asset.

        Args:
            address: Address of the account to opt in to the asset.
            suggested_params: Algorand suggested parameters for transactions.

        Returns:
            A transaction to opt-in into asset.
        """
        return transaction.AssetTransferTxn(
            sender=address,
            receiver=address,
            amt=0,
            index=self.index,
            sp=suggested_params,
        )

    def prepare_opt_out_tx(
        self, address: str, close_to: str
    ) -> transaction.AssetTransferTxn:
        """This creates a transaction that will allow the account to "opt out" of the asset.

        Args:
            address: Account to opt out of this asset.

        Returns:
            A ready to send transaction to opt-out of the ASA.
        """
        suggested_params = self.algod.suggested_params()
        return self.build_opt_out_tx(address, close_to, suggested_params)

    def build_opt_out_tx(
        self, address: str, close_to: str, suggested_params: transaction.SuggestedParams
    ) -> transaction.AssetTransferTxn:
        """Creates the actual transaction for the account to opt-out from asset.

        Args:
            address: Address of the account to opt out of the asset.
            suggested_params: Algorand suggested parameters for transactions.

        Returns:
            A transaction to opt-out of the asset.
        """
        return transaction.AssetTransferTxn(
            sender=address,
            receiver=address,
            close_assets_to=close_to,
            amt=0,
            index=self.index,
            sp=suggested_params,
        )

    def is_opted_in(self, address: str) -> bool:
        """Checks if the account is already able to hold this asset, that is it has already opted in.

        This functions should be called to check if the opt-in transaction needs to be created. See :py:meth:`pactsdk.asset.Asset.prepare_opt_in_tx`.

        Args:
            address: The account to check if the asset is opted in on.

        Returns:
            True if the account is already opted in, false otherwise.
        """
        holding = self.get_holding(address)
        return holding is not None

    def get_holding(self, address: str) -> Optional[int]:
        """Returns the amount of holding of this asset the account has.

        Note that this function may return None if the account has not opted in for this asset.

        Args:
            address: The account to check the current holding.

        Returns:
            The amount of this asset the account is holding, or None if the account is not opted into the asset.
        """
        account_info = self.algod.account_info(address)
        return self.get_holding_from_account_info(account_info)

    def get_holding_from_account_info(self, account_info: dict) -> Optional[int]:
        if self.index == 0:
            return account_info["amount"]

        for asset in account_info["assets"]:
            if asset["asset-id"] == self.index:
                return asset["amount"]

        return None

    def build_transfer_tx(
        self,
        sender: str,
        receiver: str,
        amount: int,
        suggested_params: transaction.SuggestedParams,
        note: Optional[bytes] = None,
    ) -> transaction.Transaction:
        if self.index == 0:
            # ALGO
            return transaction.PaymentTxn(
                sender=sender,
                receiver=receiver,
                amt=amount,
                note=note,
                sp=suggested_params,
            )

        return transaction.AssetTransferTxn(
            sender=sender,
            receiver=receiver,
            amt=amount,
            note=note,
            sp=suggested_params,
            index=self.index,
        )

    def __eq__(self, other_asset: object) -> bool:
        """Return equal by comparing the assets index value."""
        if not isinstance(other_asset, Asset):
            return False
        return self.index == other_asset.index

    def __repr__(self):
        if self.unit_name:
            return f"<{self.unit_name}>"
        return f"<Asset {self.index}>"

    def __hash__(self) -> int:
        return self.index
