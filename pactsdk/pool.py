import copy
from dataclasses import dataclass
from typing import Optional, Union
from urllib.parse import urlencode

import algosdk
import requests
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

from pactsdk.pool_state import AppInternalState, PoolState, parse_global_pool_state

from .asset import Asset, fetch_asset_by_index
from .exceptions import PactSdkError
from .pool_calculator import PoolCalculator
from .swap import Swap
from .transaction_group import TransactionGroup


def list_pools(pact_api_url: str, **params):
    """Returns a list of data on the pools. Note the data is json wrapped api data.

    Args:
        pact_api_url (str): Pact api base url.

    Returns:
        Any:List of json data on each pool.
    """
    assert pact_api_url
    encoded_params = urlencode(params)
    response = requests.get(f"{pact_api_url}/api/pools?{encoded_params}")
    return response.json()


def fetch_app_global_state(
    algod: AlgodClient,
    app_id: int,
) -> AppInternalState:
    """Looks up the current state of the pool represented by the app_id.

    Args:
        algod (AlgodClient): The algo client to look up the pool in.
        app_id (int): The id of the pool

    Returns:
        AppInternalState: The current internal state of the pool.
    """
    app_info = algod.application_info(app_id)
    return parse_global_pool_state(app_info["params"]["global-state"])


def fetch_pool_by_id(algod: AlgodClient, app_id: int):
    """Get the `Pool` object corresponding to the application id passed in.

    Args:
        algod (AlgodClient): The algorand client to look up the pool in.
        app_id (int): The application id for the pool to look up.

    Returns:
        Pool: The pool object for the application id passed in.
    """
    app_global_state = fetch_app_global_state(algod, app_id)

    primary_asset = fetch_asset_by_index(algod, app_global_state.ASSET_A)
    secondary_asset = fetch_asset_by_index(algod, app_global_state.ASSET_B)
    liquidity_asset = fetch_asset_by_index(algod, app_global_state.LTID)

    return Pool(
        algod=algod,
        app_id=app_id,
        primary_asset=primary_asset,
        secondary_asset=secondary_asset,
        liquidity_asset=liquidity_asset,
        internal_state=app_global_state,
        fee_bps=app_global_state.FEE_BPS,
    )


def fetch_pools_by_assets(
    algod: AlgodClient,
    asset_a: Union[Asset, int],
    asset_b: Union[Asset, int],
    pact_api_url="",
) -> list["Pool"]:
    """Return a list of pools on the api url passed in for the two assets.

    You must pass in a valid pact_api_url to look up the data. Note this will correct
    the order of assets so they will find the correct pools.

    Returns:
        list[`Pool`]: A list of pool objects that operate over the two assets.
    """
    assets = [
        asset.index if isinstance(asset, Asset) else asset
        for asset in [asset_a, asset_b]
    ]

    # Make sure that the user didn't mess up assets order.
    # Primary asset always has lower index.
    primary_asset, secondary_asset = sorted(assets)

    assert pact_api_url, "Must provide pact_api_url."

    app_ids = get_app_ids_from_assets(pact_api_url, primary_asset, secondary_asset)

    return [fetch_pool_by_id(algod, app_id) for app_id in app_ids]


def get_app_ids_from_assets(
    pact_api_url: str,
    primary_asset_index: int,
    secondary_asset_index: int,
) -> list[int]:
    """Returns a list of app ids for the pools between the two asset ids passed in.

    It does this by getting a list of all pools from the API and then extracting the appid field from
    the returned data.

    Args:
        pact_api_url (str): The url to the pact api to look up the assets.
        primary_asset_index (int): The index of the primary asset.
        secondary_asset_index (int): The index of the secondary asset.

    Returns:
        list[int]: A list of the app ids for the pools. May be empty if there are no pools.
    """
    data = list_pools(
        pact_api_url,
        primary_asset__algoid=primary_asset_index,
        secondary_asset__algoid=secondary_asset_index,
    )
    return [int(pool["appid"]) for pool in data["results"]]


@dataclass
class Pool:
    """Main data class for a liquidity pool on the PACT exchange.

    The Liquidity pool is an a pool of two assets which provides the facility to swap on asset for the other for a fee.
    The price, that is the ratio of deposited for received asset, is defined by the total ratio of the two assets.
    This amount of assets is always kept the same according to a constant formula. At the moment this formula is the
    constant product formula.

    Public Attributes:
    calculation (PoolCalculator): Utility class for calculating values for the pool.
    state (PoolState): The current state of the Pool.

    """

    algod: AlgodClient
    """The client for the Algorand where the liquidity pool is located"""
    app_id: int
    """The application id for the pool."""
    primary_asset: Asset
    """The asset of the liquidity pool with the lowest index. This is the primary asset in all functions."""
    secondary_asset: Asset
    """The asset of the liquidity pool with the second highest index. This is known as the secondary asset in all functions."""
    liquidity_asset: Asset
    """The asset code for the LP token that is given when liquidity added, and burned when liquidity is withdrawn."""
    internal_state: AppInternalState
    """The global state on the block chain for this pool."""
    fee_bps: int = 30
    """The fee in basis points for swaps trading on the pool."""

    def __post_init__(self):
        self.calculator = PoolCalculator(self)
        self.state = self.parse_internal_state(self.internal_state)

    def get_escrow_address(self):
        """Returns the Escrow account address for the Pool."""
        return algosdk.logic.get_application_address(self.app_id)

    def get_other_asset(self, asset: Asset) -> Asset:
        """Returns the other asset in the pool, that is if you put the primary asset it will return the secondary and vice versa.

        Args:
            asset (Asset): An asset in the pool that you want to find the other pool asset.

        Raises:
            PactSdkError: Raised if the asset passed in is not a pool asset.

        Returns:
            Asset: The opposite asset to the one passed in.
        """
        if asset == self.primary_asset:
            return self.secondary_asset

        if asset == self.secondary_asset:
            return self.primary_asset

        raise PactSdkError(f"Asset with index {asset.index} is not a pool asset.")

    def update_state(self) -> PoolState:
        """Updates the internal and pool state variables by re-reading the global state in the block chain.

        Returns:
            PoolState: The updated pool state read from the global state on the block chain.
        """
        self.internal_state = fetch_app_global_state(self.algod, self.app_id)
        self.state = self.parse_internal_state(self.internal_state)
        return self.state

    def prepare_add_liquidity_tx(
        self,
        address: str,
        primary_asset_amount: int,
        secondary_asset_amount: int,
    ):
        """Create the transaction group for adding the liquidity to the liquidity pool.

        Create three transactions, a deposit of the primary asset, a deposit of the secondary asset
        and an application transaction to return the liquidity asset for the deposit.

        Args:
            address (str): The account address to sign the transactions from.
            primary_asset_amount (int): The amount of primary asset to deposit
            secondary_asset_amount (int): The amount of secondary asset to deposit.

        Returns:
            TransactionGroup: The group of transactions for the transactions to add liquidity.
        """
        suggested_params = self.algod.suggested_params()

        txn1 = self._make_deposit_tx(
            address=address,
            asset=self.primary_asset,
            amount=primary_asset_amount,
            suggested_params=suggested_params,
        )
        txn2 = self._make_deposit_tx(
            address=address,
            asset=self.secondary_asset,
            amount=secondary_asset_amount,
            suggested_params=suggested_params,
        )
        txn3 = self._make_application_noop_tx(
            address=address,
            fee=3000,
            args=["ADDLIQ", 0],
            extraAsset=self.liquidity_asset,
            suggested_params=suggested_params,
        )

        return TransactionGroup([txn1, txn2, txn3])

    def prepare_remove_liquidity_tx(self, address: str, amount: int):
        """Prepares the transactions for removing liquidity from the pool, that is returning an amount of the liquidity
        pool token and receiving the primary and secondary asset.

        There are two transactions created, a deposit of the amount of liquidity pool and an application message to
        receive the pool assets.

        Args:
            address (str): The account address for signign the transactions.
            amount (int): The amount of liquidity pool tokens to return.

        Returns:
            TransactionGroup: The transaction group for removing liquidity.
        """
        suggested_params = self.algod.suggested_params()

        txn1 = self._make_deposit_tx(
            address=address,
            amount=amount,
            asset=self.liquidity_asset,
            suggested_params=suggested_params,
        )
        txn2 = self._make_application_noop_tx(
            address=address,
            fee=3000,
            args=["REMLIQ", 0, 0],  # min expected primary, min expected secondary
            suggested_params=suggested_params,
        )

        return TransactionGroup([txn1, txn2])

    def prepare_swap(self, asset: Asset, amount: int, slippage_pct: float) -> Swap:
        """Creates a new swap class for receiving the amount of asset within the slippage percent from the pool.

        Args:
            asset (Asset): The asset to receive from the pool. Must be the primary or secondary asset.
            amount (int): The amount of the asset to receive from the swap.
            slippage_pct (float): The maximum slippage allowed in the swap.

        Returns:
            Swap: The swap class for this pool.
        """
        assert self.is_asset_in_the_pool(asset), f"Asset {asset.index} not in the pool"
        return Swap(self, asset_out=asset, amount_out=amount, slippage_pct=slippage_pct)

    def prepare_swap_tx(self, swap: Swap, address: str):
        suggested_params = self.algod.suggested_params()

        txn1 = self._make_deposit_tx(
            address=address,
            amount=swap.amount_out,
            asset=swap.asset_out,
            suggested_params=suggested_params,
        )
        txn2 = self._make_application_noop_tx(
            address=address,
            fee=2000,
            args=["SWAP", swap.effect.minimum_amount_in],
            suggested_params=suggested_params,
        )

        return TransactionGroup([txn1, txn2])

    def is_asset_in_the_pool(self, asset: Asset):
        return asset.index in {self.primary_asset.index, self.secondary_asset.index}

    def parse_internal_state(self, state: AppInternalState) -> PoolState:
        return PoolState(
            total_liquidity=state.L,
            total_primary=state.A,
            total_secondary=state.B,
            primary_asset_price=self.calculator.primary_asset_price,
            secondary_asset_price=self.calculator.secondary_asset_price,
        )

    def _make_deposit_tx(
        self,
        asset: Asset,
        address: str,
        amount: int,
        suggested_params: transaction.SuggestedParams,
    ):
        if not asset.index:
            # ALGO
            return transaction.PaymentTxn(
                sender=address,
                receiver=self.get_escrow_address(),
                amt=amount,
                sp=suggested_params,
            )

        return transaction.AssetTransferTxn(
            sender=address,
            receiver=self.get_escrow_address(),
            amt=amount,
            sp=suggested_params,
            index=asset.index,
        )

    def _make_application_noop_tx(
        self,
        address: str,
        args: list,
        fee: int,
        suggested_params: transaction.SuggestedParams,
        extraAsset: Optional[Asset] = None,
    ):
        foreign_assets: list[int] = [
            self.primary_asset.index,
            self.secondary_asset.index,
        ]
        if extraAsset:
            foreign_assets.append(extraAsset.index)

        suggested_params = copy.copy(suggested_params)
        suggested_params.fee = fee
        suggested_params.flat_fee = True

        return transaction.ApplicationNoOpTxn(
            sender=address,
            index=self.app_id,
            foreign_assets=foreign_assets,
            app_args=args,
            sp=suggested_params,
        )
