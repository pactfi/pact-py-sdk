import copy
import math
from dataclasses import dataclass, field
from typing import Literal, Optional, Union

import algosdk
from algosdk import transaction
from algosdk.v2client.algod import AlgodClient

from pactsdk.api import ListPoolsParams, list_pools
from pactsdk.constant_product_calculator import ConstantProductParams
from pactsdk.pool_state import (
    AppInternalState,
    PoolState,
    get_pool_type_from_internal_state,
    parse_global_pool_state,
)
from pactsdk.stableswap_calculator import StableswapParams

from .add_liquidity import LiquidityAddition
from .asset import Asset, fetch_asset_by_index
from .exceptions import PactSdkError
from .pool_calculator import PoolCalculator
from .swap import Swap
from .transaction_group import TransactionGroup
from .zap import Zap

PoolType = Literal["CONSTANT_PRODUCT", "NFT_CONSTANT_PRODUCT", "STABLESWAP"]

OperationType = Literal["SWAP", "ADDLIQ", "REMLIQ"]
"""The basic three operation types in a PACT liquidity pool, namely Add Liquidity (ADDLIQ), Remove Liquidity (REMLIQ) and making a swap (SWAP)."""


def fetch_app_global_state(
    algod: AlgodClient,
    app_id: int,
) -> AppInternalState:
    """Fetches the global state of the of an application.

    Args:
        algod: The algo client to query the app in.
        app_id: The application id to fetch the state of.

    Returns:
        The global state of the application.
    """
    app_info = algod.application_info(app_id)
    return parse_global_pool_state(app_info["params"]["global-state"])


def fetch_pool_by_id(algod: AlgodClient, app_id: int):
    """Fetches the pool from the blockchain using the provided algod client.

    Args:
        algod: The algo client to use.
        app_id: The application id to fetch.

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
    )


def fetch_pools_by_assets(
    algod: AlgodClient,
    asset_a: Union[Asset, int],
    asset_b: Union[Asset, int],
    pact_api_url: str,
) -> list["Pool"]:
    """Returns the list of pools for the assets passed in.

    There can be zero pools if there are no pools matching the assets, or multiple if there are multiple at different fees.
    The order of assets that you provide is irrelevant.

    Args:
        algod: The algo client to use.
        asset_a: One of the assets in the pool (asset id or asset instance).
        asset_b: The other asset in the pool (asset id or asset instance).
        pact_api_url: The API url to use.

    Returns:
        A list of pools matching the provided assets.
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
    """Returns the application ids for any pools that match the primary and secondary asset.

    This function finds any pools using the `pact_api_url` passed in that match the asset ids passed in.

    Args:
        pact_api_url: The API url to use.
        primary_asset_index: The asset id for the primary asset of the pool.
        secondary_asset_index: The asset id for the secondary asset of the pool.

    Returns:
        List of asset ids.
    """
    params: ListPoolsParams = {
        "primary_asset__on_chain_id": primary_asset_index,
        "secondary_asset__on_chain_id": secondary_asset_index,
    }
    data = list_pools(pact_api_url, params)
    return [int(pool["on_chain_id"]) for pool in data["results"]]


@dataclass
class Pool:
    """Pool represents a liquidity pool in the PACT AMM.

    Typically, users don't have to instantiate this class manually. Use :py:meth:`pactsdk.client.PactClient.fetch_pool_by_id` or :py:meth:`pactsdk.client.PactClient.fetch_pools_by_assets` instead.

    The primary methods of the pool are to create the transaction groups to enable you to:

    - Add Liquidity,
    - Removing Liquidity,
    - Create a Swap on the Pool.
    """

    algod: AlgodClient
    """The Algorand client to use."""

    app_id: int
    """The application id for the pool."""

    primary_asset: Asset
    """The asset of the liquidity pool with the lower index."""

    secondary_asset: Asset
    """The asset of the liquidity pool with the higher index."""

    liquidity_asset: Asset
    """The asset for the liquidity pool token (LP token) that is given when liquidity is added, and burned when liquidity is withdrawn."""

    internal_state: AppInternalState
    """The global state on the blockchain for this pool."""

    fee_bps: int = 30
    """The fee in basis points for swaps trading on the pool."""

    pool_type: PoolType = field(init=False)
    """Different pool types use different formulas for making swaps."""

    version: int = field(init=False)
    """The version of the contract. May be 0 for some old pools which don't expose the version in the global state."""

    def __post_init__(self):
        self.params: Union[StableswapParams, ConstantProductParams]

        self.pool_type = get_pool_type_from_internal_state(self.internal_state)

        if self.pool_type in ["CONSTANT_PRODUCT", "NFT_CONSTANT_PRODUCT"]:
            self.params = ConstantProductParams(
                fee_bps=self.internal_state.FEE_BPS,
                pact_fee_bps=self.internal_state.PACT_FEE_BPS or 0,
            )
        elif self.pool_type == "STABLESWAP":
            self.params = StableswapParams(
                fee_bps=self.internal_state.FEE_BPS,
                pact_fee_bps=self.internal_state.PACT_FEE_BPS or 0,
                initial_a=self.internal_state.INITIAL_A or 0,
                initial_a_time=self.internal_state.INITIAL_A_TIME or 0,
                future_a=self.internal_state.FUTURE_A or 0,
                future_a_time=self.internal_state.FUTURE_A_TIME or 0,
                precision=self.internal_state.PRECISION or 1,
            )
        else:
            raise PactSdkError(f'Unknown pool type "{self.pool_type}".')

        self.fee_bps = self.internal_state.FEE_BPS
        self.version = self.internal_state.VERSION or 0

        self.calculator = PoolCalculator(self)
        self.state = self.parse_internal_state(self.internal_state)

    def __eq__(self, other_pool: object) -> bool:
        """Return equal by comparing the pools app_id value."""
        if not isinstance(other_pool, Pool):
            return False
        return self.app_id == other_pool.app_id

    def get_escrow_address(self) -> str:
        """Get the escrow address of the pool.

        Returns:
            The address corresponding to that pools's escrow account.
        """
        return algosdk.logic.get_application_address(self.app_id)

    def get_other_asset(self, asset: Asset) -> Asset:
        """Returns the "other" asset, i.e. primary if secondary is passed in and vice versa.

        Args:
            asset: The primary or secondary asset of the pool.

        Raises:
            PactSdkError: If the asset passed in is not the primary or secondary asset.

        Returns:
            The other asset, if the primary asset was passed in it will be the secondary asset and vice versa.
        """
        if asset == self.primary_asset:
            return self.secondary_asset

        if asset == self.secondary_asset:
            return self.primary_asset

        raise PactSdkError(f"Asset with index {asset.index} is not a pool asset.")

    def update_state(self) -> PoolState:
        """Updates the internal and pool state properties by re-reading the global state in the blockchain.

        Updating the pool state is recommended if there is a pause between the construction of the pool and the creation of the transactions on the pool. Calling this method ensures that the the pool state is not stale.

        Returns:
            The new pool state.
        """
        self.internal_state = fetch_app_global_state(self.algod, self.app_id)
        self.state = self.parse_internal_state(self.internal_state)
        return self.state

    def prepare_add_liquidity(
        self,
        primary_asset_amount: int,
        secondary_asset_amount: int,
        slippage_pct: float,
    ) -> LiquidityAddition:
        """
        Creates a new LiquidityAddition instance.

        Args:
            options: Options for adding the liquidity.

        Returns:
            A new LiquidityAddition object.
        """
        return LiquidityAddition(
            pool=self,
            primary_asset_amount=primary_asset_amount,
            secondary_asset_amount=secondary_asset_amount,
            slippage_pct=slippage_pct,
        )

    def prepare_add_liquidity_tx_group(
        self,
        address: str,
        liquidity_addition: LiquidityAddition,
    ) -> TransactionGroup:
        """Prepares a :py:class:`pactsdk.transaction_group.TransactionGroup` for adding liquidity to the pool. See :py:meth:`pactsdk.pool.Pool.buildAddLiquidityTxs` for details.

        Args:
            address: Account address that will deposit the primary and secondary assets and receive the LP token.
            primary_asset_amount: The amount of primary asset to deposit.
            secondary_asset_amount: The amount of secondary asset to deposit.

        Returns:
            A transaction group that when executed will add liquidity to the pool.
        """
        suggested_params = self.algod.suggested_params()
        txs = self.build_add_liquidity_txs(
            address, liquidity_addition, suggested_params
        )
        return TransactionGroup(txs)

    def build_add_liquidity_txs(
        self,
        address: str,
        liquidity_addition: LiquidityAddition,
        suggested_params: transaction.SuggestedParams,
    ) -> list[transaction.Transaction]:
        """Builds the transactions to add liquidity for the primary asset and secondary asset of the pool.

        In typical circumstances 3 transactions are generated:

        - deposit of asset A
        - deposit of asset B
        - "ADDLIQ" application call to add liquidity with the above deposits

        The initial liquidity must satisfy the expression `sqrt(a * b) - 1000 > 0`.

        Args:
            address: Account address that will deposit the primary and secondary assets and receive the LP token.
            primary_asset_amount: The amount of primary asset to deposit.
            secondary_asset_amount: The amount of secondary asset to deposit.
            suggested_params: Algorand suggested parameters for transactions.
            note: An optional note that can be added to the application ADDLIQ transaction.

        Raises:
            AssertionError: If initial liquidity is too low.

        Returns:
            List of transactions to add the liquidity.
        """
        primary_asset_amount = liquidity_addition.primary_asset_amount
        secondary_asset_amount = liquidity_addition.secondary_asset_amount

        if self.calculator.is_empty:
            assert (
                math.isqrt(primary_asset_amount * secondary_asset_amount) - 1000 > 0
            ), "Initial liquidity must satisfy the expression `sqrt(a * b) - 1000 > 0`"

        return self.build_raw_add_liquidity_txs(
            address=address,
            primary_asset_amount=primary_asset_amount,
            secondary_asset_amount=secondary_asset_amount,
            minimum_minted_liquidity_tokens=liquidity_addition.effect.minimum_minted_liquidity_tokens,
            suggested_params=suggested_params,
            fee=liquidity_addition.effect.tx_fee,
        )

    def build_raw_add_liquidity_txs(
        self,
        address: str,
        primary_asset_amount: int,
        secondary_asset_amount: int,
        minimum_minted_liquidity_tokens: int,
        suggested_params: transaction.SuggestedParams,
        fee: int,
        note=b"",
    ):
        tx1 = self._make_deposit_tx(
            address=address,
            asset=self.primary_asset,
            amount=primary_asset_amount,
            note=note or b"Pact add liquidity deposit",
            suggested_params=suggested_params,
        )
        tx2 = self._make_deposit_tx(
            address=address,
            asset=self.secondary_asset,
            amount=secondary_asset_amount,
            note=note or b"Pact add liquidity deposit",
            suggested_params=suggested_params,
        )
        tx3 = self._make_application_noop_tx(
            address=address,
            fee=fee,
            args=["ADDLIQ", minimum_minted_liquidity_tokens],
            extraAsset=self.liquidity_asset,
            suggested_params=suggested_params,
            note=note,
        )

        return [tx1, tx2, tx3]

    def prepare_remove_liquidity_tx_group(
        self, address: str, amount: int
    ) -> TransactionGroup:
        """Prepares the transaction group for removing liquidity from the pool.

        Args:
            address: Account address that will deposit the LP token and receive the primary and secondary assets.
            amount: The amount of the LP token to return to the pool.

        Returns:
            Transaction group that when executed will remove liquidity from the pool.
        """
        suggested_params = self.algod.suggested_params()
        txs = self.build_remove_liquidity_txs(address, amount, suggested_params)
        return TransactionGroup(txs)

    def build_remove_liquidity_txs(
        self, address: str, amount: int, suggested_params: transaction.SuggestedParams
    ) -> list[transaction.Transaction]:
        """This creates two transactions in a group for the remove operation.

        - deposit of the liquidity asset
        - "REMLIQ" application call to remove the LP token from the account and receive the deposited assets in return.

        Args:
            address: Account address that will deposit the LP token and receive the primary and secondary assets.
            amount: The amount of the LP token to return to the pool.
            suggested_params: Algorand suggested parameters for transactions.

        Returns:
            List of transactions to remove the liquidity.
        """
        tx1 = self._make_deposit_tx(
            address=address,
            amount=amount,
            asset=self.liquidity_asset,
            note=b"Pact remove liquidity deposit",
            suggested_params=suggested_params,
        )
        tx2 = self._make_application_noop_tx(
            address=address,
            fee=3000,
            args=["REMLIQ", 0, 0],  # min expected primary, min expected secondary
            suggested_params=suggested_params,
        )

        return [tx1, tx2]

    def prepare_swap(
        self, asset: Asset, amount: int, slippage_pct: float, swap_for_exact=False
    ) -> Swap:
        """Creates a new swap instance for receiving the amount of asset within the slippage percent from the pool.

        Args:
            asset: The asset to swap.
            amount: Amount to swap or to receive. Look at `swap_for_exact` flag for details.
            slippage_pct: The maximum allowed slippage in percents e.g. `10` is 10%. The swap will fail if the slippage will be higher.
            swap_for_exact: If false or not provided, the `amount` is the amount to swap (deposit in the contract). If true, the `amount` is the amount to receive from the swap.

        Returns:
            A new swap object.
        """
        assert self.is_asset_in_the_pool(asset), f"Asset {asset.index} not in the pool"
        return Swap(
            self,
            asset_deposited=asset,
            amount=amount,
            slippage_pct=slippage_pct,
            swap_for_exact=swap_for_exact,
        )

    def prepare_swap_tx_group(self, swap: Swap, address: str) -> TransactionGroup:
        """Prepares a transaction group that when executed will perform a swap on the pool.

        Args:
            swap: The swap for which to generate transactions.
            address: The address that is performing the swap.

        Returns:
            Transaction group that when executed will perform a swap on the pool.
        """
        suggested_params = self.algod.suggested_params()
        txs = self.build_swap_txs(swap, address, suggested_params)
        return TransactionGroup(txs)

    def build_swap_txs(
        self, swap: Swap, address: str, suggested_params: transaction.SuggestedParams
    ) -> list[transaction.Transaction]:
        """Builds two transactions:

        - deposit of the asset to swap
        - "SWAP' application call that performs the swap to receive the other asset

        Args:
            swap: The swap for which to generate transactions.
            address: The address that is performing the swap.
            suggested_params: Algorand suggested parameters for transactions.

        Returns:
            List of transactions to perform the swap.
        """
        tx1 = self._make_deposit_tx(
            address=address,
            amount=swap.effect.amount_deposited,
            asset=swap.asset_deposited,
            note=b"Pact swap deposit",
            suggested_params=suggested_params,
        )
        tx2 = self._make_application_noop_tx(
            address=address,
            fee=swap.effect.tx_fee,
            args=["SWAP", swap.effect.minimum_amount_received],
            suggested_params=suggested_params,
        )

        return [tx1, tx2]

    def is_asset_in_the_pool(self, asset: Asset) -> bool:
        """Check if the asset is the primary or secondary asset of this pool.

        Args:
            asset: The asset to check is in the pool.

        Returns:
            True if the asset is in the pool or False otherwise.
        """
        return asset.index in {self.primary_asset.index, self.secondary_asset.index}

    def parse_internal_state(self, state: AppInternalState) -> PoolState:
        """Read the new pool state from the global state of the application.

        Args:
            state: Global state for the application.

        Returns:
            Parsed state.
        """
        return PoolState(
            total_liquidity=state.L,
            total_primary=state.A,
            total_secondary=state.B,
            primary_asset_price=self.calculator.primary_asset_price,
            secondary_asset_price=self.calculator.secondary_asset_price,
        )

    def prepare_zap(self, asset: Asset, amount: int, slippage_pct: float) -> Zap:
        """Creates a new zap instance for getting all required data for performing a zap.

        Args:
            asset: The asset to zap.
            amount: Amount used for the zap.
            slippage_pct: The maximum allowed slippage in percents e.g. `10` is 10%. The swap will fail if the slippage will be higher.

        Returns:
            A new zap object.
        """
        return Zap(
            self,
            asset=asset,
            amount=amount,
            slippage_pct=slippage_pct,
        )

    def prepare_zap_tx_group(self, zap: Zap, address: str) -> TransactionGroup:
        """Prepares a transaction group that when executed will perform a Zap on the pool.

        Args:
            zap: The zap for which to generate transactions.
            address: The address that is performing the Zap.

        Returns:
            Transaction group that when executed will perform a Zap on the pool.
        """
        suggested_params = self.algod.suggested_params()
        txs = self.build_zap_txs(zap, address, suggested_params)
        return TransactionGroup(txs)

    def build_zap_txs(
        self, zap: Zap, address: str, suggested_params: transaction.SuggestedParams
    ) -> list[transaction.Transaction]:
        """Builds the transactions to perform a Zap on the pool as per the options passed in. Zap allows to add liquidity to the pool by providing only one asset.

        This function will generate swap Txs to get a proper amount of the second asset and then generate add liquidity Txs with both of those assets.
        See :py:meth:`pactsdk.pool.Pool.buildSwapTxs` and :py:meth:`pactsdk.pool.Pool.buildAddLiquidityTxs` for more details.

        This feature is supposed to work with constant product pools only. Stableswaps can accept one asset to add liquidity by default.

        Args:
            zap: The zap for which to generate transactions.
            address: The address that is performing the Zap.
            suggested_params: Algorand suggested parameters for transactions.

        Returns:
            List of transactions to perform the Zap.
        """
        swap_txs = self.build_swap_txs(zap.swap, address, suggested_params)
        add_liq_txs = self.build_add_liquidity_txs(
            address, zap.liquidity_addition, suggested_params
        )
        return [*swap_txs, *add_liq_txs]

    def _make_deposit_tx(
        self,
        asset: Asset,
        address: str,
        amount: int,
        note: bytes,
        suggested_params: transaction.SuggestedParams,
    ):
        return asset.build_transfer_tx(
            sender=address,
            receiver=self.get_escrow_address(),
            amount=amount,
            note=note,
            suggested_params=suggested_params,
        )

    def _make_application_noop_tx(
        self,
        address: str,
        args: list,
        fee: int,
        suggested_params: transaction.SuggestedParams,
        extraAsset: Optional[Asset] = None,
        note=b"",
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
            note=note,
        )
