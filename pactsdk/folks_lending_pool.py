"""
This module allows for composing Pact swaps and adding/removing liquidity with Folks Finance lending pools, resulting in a higher APR for liquidity providers that accommodates both, the trading APR and the lending APR.

The user is not interacting with Folks Finance pools or Pact pools directly. Instead, the user is calling a global adapter contract that makes inner transactions to the other applications.

The Pact pool is between two fAssets e.g. fALGO and fUSDC but the user doesn't have to be opted into those fAssets. The user interacts only with ALGO and USDC. Converting between the original assets and fAssets is hidden in the adapter contract.

To add liquidity:
 - The user deposits ALGO and USDC in the adapter contract.
 - The user calls “pre_add_liquidity” method on the adapter.
 - The adapter converts ALGO to fALGO and USDC to fUSDC in corresponding Folks Finance pools.
 - The user calls “add_liquidity” method on the adapter.
 - The adapter deposits fALGO and fUSDC in Pact pool and receives liquidity tokens in return.
 - The adapter transfers the liquidity tokens to the user.

To remove liquidity:
 - The user deposits liquidity tokens in the adapter contract.
 - The user calls “remove_liquidity” method on the adapter.
 - The adapter removes liquidity from the Pact pool and receives fALGO and fUSDC in return.
 - The user calls “post_remove_liquidity” method on the adapter.
 - The adapter converts fALGO to ALGO and fUSDC to USDC in corresponding Folks Finance pools.
 - The adapter transfers ALGO and USDC tokens to the user.

For swap:
 - The user deposits one of the assets in the adapter e.g. USDC.
 - The user calls “swap” method on the adapter.
 - The adapter converts USDC to fUSDC in a corresponding Folks Finance pool.
 - The adapter swaps fUSDC to fALGO in a Pact pool.
 - The adapter converts fALGO to ALGO in a corresponding Folks Finance pool.
 - The adapter transfers ALGO to the user.
"""

import base64
import dataclasses
import datetime
import math
from typing import Optional

import algosdk
from algosdk.v2client.algod import AlgodClient

from .add_liquidity import LiquidityAddition
from .asset import Asset, fetch_asset_by_index
from .encoding import extract_uint64
from .pool import Pool
from .swap import Swap
from .transaction_group import TransactionGroup
from .utils import get_selector, parse_app_state, sp_fee

PRE_ADD_LIQUIDITY_SIG = get_selector(
    "pre_add_liquidity(txn,txn,asset,asset,asset,asset,application,application,application,application)void"
)
ADD_LIQUIDITY_SIG = get_selector(
    "add_liquidity(asset,asset,asset,application,uint64)void"
)
REMOVE_LIQUIDITY_SIG = get_selector(
    "remove_liquidity(axfer,asset,asset,asset,application)void"
)
POST_REMOVE_LIQUIDITY_SIG = get_selector(
    "post_remove_liquidity(asset,asset,asset,asset,application,application,application,uint64,uint64)void"
)
SWAP_SIG = get_selector(
    "swap(txn,asset,asset,asset,asset,application,application,application,application,uint64)void"
)
OPT_IN_SIG = get_selector("opt_in(uint64[])void")

ABI_BYTE = algosdk.abi.UintType(8)

# call(1000) + 2 * wrap(4000) + refund(1000)
PRE_ADD_LIQ_FEE = 10_000

# call(1000) + 2 * wrap(4000)
ADD_LIQ_FEE = 9000

# call(1000) + transfer_PLP(1000) + rem_liq(3000)
REM_LIQ_FEE = 5000

# call(1000) + 2 * unwrap(5000) + 2 * transfer_asset(1000)
POST_REM_LIQ_FEE = 13_000

# call(1000) + wrap(4000) + swap(3000) + unwrap(5000) + transfer_asset(1000)
SWAP_FEE = 14_000

SECONDS_IN_YEAR = 365 * 24 * 60 * 60
ONE_14_DP = int(1e14)
ONE_16_DP = int(1e16)


@dataclasses.dataclass
class FolksLendingPool:
    algod: AlgodClient
    app_id: int
    manager_app_id: int
    deposit_interest_rate: int
    deposit_interest_index: int
    updated_at: datetime.datetime
    original_asset: Asset
    f_asset: Asset
    escrow_address: str = dataclasses.field(init=False)

    last_timestamp_override: Optional[int] = None
    """The conversion calculations are dependant of precise timestamps. The Folks contract uses the last block timestamp for this value. The SDK, by default, uses current system time. This field allows to override the default behavior. This is needed in unit tests and normal users should leave this field as None."""

    def __post_init__(self):
        self.escrow_address = algosdk.logic.get_application_address(self.app_id)

    def _calc_deposit_interest_index(self, timestamp: int) -> int:
        dt = timestamp - int(self.updated_at.timestamp())
        return (
            self.deposit_interest_index
            * (ONE_16_DP + (self.deposit_interest_rate * dt // SECONDS_IN_YEAR))
            // ONE_16_DP
        )

    def convert_deposit(self, amount: int) -> int:
        """Calculates the amount fAsset received when depositing original asset."""
        interest_index = self._calc_deposit_interest_index(self.get_last_timestamp())
        return amount * ONE_14_DP // interest_index

    def convert_withdraw(self, amount: int, ceil=False) -> int:
        """Calculates the amount original asset received when depositing fAsset."""
        interest_index = self._calc_deposit_interest_index(self.get_last_timestamp())
        converted = amount * interest_index / ONE_14_DP
        if ceil:
            return math.ceil(converted)
        return math.floor(converted)

    def get_last_timestamp(self) -> int:
        return self.last_timestamp_override or int(datetime.datetime.now().timestamp())


def fetch_folks_lending_pool(algod: AlgodClient, app_id: int) -> FolksLendingPool:
    """Fetches Folks lending pool application info from the algod, parses the global state and builds FolksLendingPool object."""
    app_info = algod.application_info(app_id)
    raw_state = app_info["params"]["global-state"]
    state = parse_app_state(raw_state)

    manager_app_id = extract_uint64(base64.b64decode(state["pm"]), 0)

    assets_ids = base64.b64decode(state["a"])
    original_asset_id = extract_uint64(assets_ids, 0)
    f_asset_id = extract_uint64(assets_ids, 8)

    interest_info = base64.b64decode(state["i"])
    deposit_interest_rate = extract_uint64(interest_info, 32)
    deposit_interest_index = extract_uint64(interest_info, 40)

    updated_at = extract_uint64(interest_info, 48)

    original_asset = fetch_asset_by_index(algod, original_asset_id)
    f_asset = fetch_asset_by_index(algod, f_asset_id)

    return FolksLendingPool(
        algod=algod,
        app_id=app_id,
        manager_app_id=manager_app_id,
        deposit_interest_rate=deposit_interest_rate,
        deposit_interest_index=deposit_interest_index,
        updated_at=datetime.datetime.fromtimestamp(
            updated_at, tz=datetime.timezone.utc
        ),
        original_asset=original_asset,
        f_asset=f_asset,
    )


@dataclasses.dataclass
class LendingLiquidityAddition:
    """A wrapper around LiquidityAddition object that converts assets to fAssets before creating LiquidityAddition object."""

    lending_pool_adapter: "FolksLendingPoolAdapter"

    primary_asset_amount: int
    """Amount of original primary asset deposited."""

    secondary_asset_amount: int
    """Amount of original secondary asset deposited."""

    slippage_pct: float
    """The maximum amount of slippage allowed in performing the add liquidity."""

    liquidity_addition: LiquidityAddition = dataclasses.field(init=False)
    """Information about actual add liquidity operation on the Pact pool."""

    def __post_init__(self):
        self.liquidity_addition = LiquidityAddition(
            pool=self.lending_pool_adapter.pact_pool,
            primary_asset_amount=self.lending_pool_adapter.primary_lending_pool.convert_deposit(
                self.primary_asset_amount
            ),
            secondary_asset_amount=self.lending_pool_adapter.secondary_lending_pool.convert_deposit(
                self.secondary_asset_amount
            ),
            slippage_pct=self.slippage_pct,
        )
        self.liquidity_addition.effect.tx_fee = PRE_ADD_LIQ_FEE + ADD_LIQ_FEE


@dataclasses.dataclass
class LendingSwap:
    """A wrapper around Swap object that adds some lending specific information."""

    f_swap: Swap
    """Information about the actual swap on the Pact pool."""

    asset_deposited: Asset
    asset_received: Asset

    amount_deposited: int
    """Amount of original asset deposited by the user."""

    amount_received: int
    """Amount of original asset received by the user."""

    minimum_amount_received: int
    """Minimal amount of original asset received by the user after the slippage."""

    tx_fee: int


@dataclasses.dataclass
class FolksLendingPoolAdapter:
    """The representation of the adapter contract.

    It allows adding/removing liquidity and making swaps using a combination Pact pool and Folks Finance lending pools.

    This class tries to mimic the interface of a :py:class:`pactsdk.pool.Pool` for making the above operations.
    """

    algod: AlgodClient
    app_id: int
    pact_pool: Pool
    primary_lending_pool: FolksLendingPool
    secondary_lending_pool: FolksLendingPool
    escrow_address: str = dataclasses.field(init=False)

    def __post_init__(self):
        assert (
            self.pact_pool.primary_asset.index
            == self.primary_lending_pool.f_asset.index
        )
        assert (
            self.pact_pool.secondary_asset.index
            == self.secondary_lending_pool.f_asset.index
        )
        assert (
            self.primary_lending_pool.manager_app_id
            == self.secondary_lending_pool.manager_app_id
        )
        self.escrow_address = algosdk.logic.get_application_address(self.app_id)

    def original_asset_to_f_asset(self, original_asset: Asset) -> Asset:
        assets_map = {
            self.primary_lending_pool.original_asset: self.primary_lending_pool.f_asset,
            self.secondary_lending_pool.original_asset: self.secondary_lending_pool.f_asset,
        }
        return assets_map[original_asset]

    def f_asset_to_original_asset(self, f_asset: Asset) -> Asset:
        assets_map = {
            self.primary_lending_pool.f_asset: self.primary_lending_pool.original_asset,
            self.secondary_lending_pool.f_asset: self.secondary_lending_pool.original_asset,
        }
        return assets_map[f_asset]

    def prepare_add_liquidity(
        self,
        primary_asset_amount: int,
        secondary_asset_amount: int,
        slippage_pct: float,
    ) -> LendingLiquidityAddition:
        return LendingLiquidityAddition(
            lending_pool_adapter=self,
            primary_asset_amount=primary_asset_amount,
            secondary_asset_amount=secondary_asset_amount,
            slippage_pct=slippage_pct,
        )

    def prepare_add_liquidity_tx_group(
        self,
        address: str,
        liquidity_addition: LendingLiquidityAddition,
    ) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_add_liquidity_txs(
            address, liquidity_addition, suggested_params
        )
        return TransactionGroup(txs)

    def build_add_liquidity_txs(
        self,
        address: str,
        liquidity_addition: LendingLiquidityAddition,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[algosdk.transaction.Transaction]:
        tx1 = self.primary_lending_pool.original_asset.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=liquidity_addition.primary_asset_amount,
            suggested_params=suggested_params,
        )

        tx2 = self.secondary_lending_pool.original_asset.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=liquidity_addition.secondary_asset_amount,
            suggested_params=suggested_params,
        )

        tx3 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, PRE_ADD_LIQ_FEE),
            index=self.app_id,
            app_args=[
                PRE_ADD_LIQUIDITY_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2, 3]],  # assets
                *[ABI_BYTE.encode(v) for v in [1, 2, 3, 4]],  # apps
            ],
            foreign_assets=[
                self.primary_lending_pool.original_asset.index,
                self.secondary_lending_pool.original_asset.index,
                self.primary_lending_pool.f_asset.index,
                self.secondary_lending_pool.f_asset.index,
            ],
            foreign_apps=[
                self.primary_lending_pool.app_id,
                self.secondary_lending_pool.app_id,
                self.primary_lending_pool.manager_app_id,
                self.pact_pool.app_id,
            ],
        )

        tx4 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, ADD_LIQ_FEE),
            index=self.app_id,
            app_args=[
                ADD_LIQUIDITY_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2]],  # assets
                ABI_BYTE.encode(1),  # pact pool id
                0,  # min expected
            ],
            foreign_assets=[
                self.primary_lending_pool.f_asset.index,
                self.secondary_lending_pool.f_asset.index,
                self.pact_pool.liquidity_asset.index,
            ],
            foreign_apps=[
                self.pact_pool.app_id,
            ],
        )

        return [tx1, tx2, tx3, tx4]

    def prepare_remove_liquidity_tx_group(
        self, address: str, amount: int
    ) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_remove_liquidity_txs(address, amount, suggested_params)
        return TransactionGroup(txs)

    def build_remove_liquidity_txs(
        self,
        address: str,
        amount: int,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[algosdk.transaction.Transaction]:
        tx1 = self.pact_pool.liquidity_asset.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=amount,
            suggested_params=suggested_params,
        )

        tx2 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, REM_LIQ_FEE),
            index=self.app_id,
            app_args=[
                REMOVE_LIQUIDITY_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2]],  # assets
                ABI_BYTE.encode(1),  # pact pool
            ],
            foreign_assets=[
                self.primary_lending_pool.f_asset.index,
                self.secondary_lending_pool.f_asset.index,
                self.pact_pool.liquidity_asset.index,
            ],
            foreign_apps=[
                self.pact_pool.app_id,
            ],
        )

        tx3 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, POST_REM_LIQ_FEE),
            index=self.app_id,
            app_args=[
                POST_REMOVE_LIQUIDITY_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2, 3]],  # assets
                *[ABI_BYTE.encode(v) for v in [1, 2, 3]],  # apps
                0,  # min expected primary
                0,  # min expected secondary
            ],
            foreign_assets=[
                self.primary_lending_pool.original_asset.index,
                self.secondary_lending_pool.original_asset.index,
                self.primary_lending_pool.f_asset.index,
                self.secondary_lending_pool.f_asset.index,
            ],
            foreign_apps=[
                self.primary_lending_pool.app_id,
                self.secondary_lending_pool.app_id,
                self.primary_lending_pool.manager_app_id,
            ],
        )

        return [tx1, tx2, tx3]

    def prepare_swap(
        self, asset: Asset, amount: int, slippage_pct: float, swap_for_exact=False
    ) -> LendingSwap:
        f_asset = self.original_asset_to_f_asset(asset)

        if asset == self.primary_lending_pool.original_asset:
            deposited_lending_pool = self.primary_lending_pool
            received_lending_pool = self.secondary_lending_pool
        else:
            deposited_lending_pool = self.secondary_lending_pool
            received_lending_pool = self.primary_lending_pool

        if swap_for_exact:
            f_amount = received_lending_pool.convert_deposit(amount)
        else:
            f_amount = deposited_lending_pool.convert_deposit(amount)

        f_swap = self.pact_pool.prepare_swap(
            f_asset, f_amount, slippage_pct, swap_for_exact
        )

        asset_deposited = self.f_asset_to_original_asset(f_swap.asset_deposited)
        asset_received = self.f_asset_to_original_asset(f_swap.asset_received)

        if swap_for_exact:
            amount_deposited = deposited_lending_pool.convert_withdraw(
                f_swap.effect.amount_deposited, ceil=True
            )
            amount_received = amount
        else:
            amount_deposited = amount
            amount_received = received_lending_pool.convert_withdraw(
                f_swap.effect.amount_received
            )

        minimum_amount_received = received_lending_pool.convert_withdraw(
            f_swap.effect.minimum_amount_received
        )

        tx_fee = SWAP_FEE + 1000  # + deposit(1000)

        return LendingSwap(
            f_swap=f_swap,
            asset_deposited=asset_deposited,
            asset_received=asset_received,
            amount_deposited=amount_deposited,
            amount_received=amount_received,
            minimum_amount_received=minimum_amount_received,
            tx_fee=tx_fee,
        )

    def prepare_swap_tx_group(
        self, swap: LendingSwap, address: str
    ) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_swap_txs(swap, address, suggested_params)
        return TransactionGroup(txs)

    def build_swap_txs(
        self,
        swap: LendingSwap,
        address: str,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[algosdk.transaction.Transaction]:
        tx1 = swap.asset_deposited.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=swap.amount_deposited,
            suggested_params=suggested_params,
        )

        tx2 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, SWAP_FEE),
            index=self.app_id,
            app_args=[
                SWAP_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2, 3]],  # assets
                *[ABI_BYTE.encode(v) for v in [1, 2, 3, 4]],  # apps
                swap.minimum_amount_received,
            ],
            foreign_assets=[
                self.primary_lending_pool.original_asset.index,
                self.secondary_lending_pool.original_asset.index,
                self.primary_lending_pool.f_asset.index,
                self.secondary_lending_pool.f_asset.index,
            ],
            foreign_apps=[
                self.primary_lending_pool.app_id,
                self.secondary_lending_pool.app_id,
                self.primary_lending_pool.manager_app_id,
                self.pact_pool.app_id,
            ],
        )

        return [tx1, tx2]

    def prepare_opt_in_to_asset_tx_group(
        self, address: str, asset_ids: list[int]
    ) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_opt_in_to_asset_tx_group(address, asset_ids, suggested_params)
        return TransactionGroup(txs)

    def build_opt_in_to_asset_tx_group(
        self,
        address: str,
        asset_ids: list[int],
        suggested_params: algosdk.transaction.SuggestedParams,
    ):
        assert 0 < len(asset_ids) <= 8

        asset_ids = [asset_id for asset_id in asset_ids if asset_id > 0]

        tx1 = algosdk.transaction.PaymentTxn(
            sender=address,
            receiver=self.escrow_address,
            amt=100_000 + len(asset_ids) * 100_000,
            sp=suggested_params,
        )

        tx2 = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, 1000 + 1000 * len(asset_ids)),
            index=self.app_id,
            app_args=[
                OPT_IN_SIG,
                algosdk.abi.ArrayDynamicType(algosdk.abi.UintType(64)).encode(
                    asset_ids
                ),
            ],
            foreign_assets=asset_ids,
        )

        return [tx1, tx2]
