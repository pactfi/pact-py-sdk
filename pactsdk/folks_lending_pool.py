import base64
import dataclasses
import datetime

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

    def calc_deposit_interest_rate(self, timestamp: datetime.datetime) -> int:
        dt = int((timestamp - self.updated_at).total_seconds())
        return (
            self.deposit_interest_index
            * (ONE_16_DP + (self.deposit_interest_rate * dt // SECONDS_IN_YEAR))
            // ONE_16_DP
        )

    def convert_deposit(self, amount: int) -> int:
        rate = self.calc_deposit_interest_rate(datetime.datetime.now())
        return amount * ONE_14_DP // rate

    def convert_withdraw(self, amount: int) -> int:
        rate = self.calc_deposit_interest_rate(datetime.datetime.now())
        return amount * rate // ONE_14_DP


def fetch_folks_lending_pool(algod: AlgodClient, app_id: int) -> FolksLendingPool:
    """Fetches lending pool's global state and extract the three important integers"""
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
        updated_at=datetime.datetime.fromtimestamp(updated_at),
        original_asset=original_asset,
        f_asset=f_asset,
    )


@dataclasses.dataclass
class LendingLiquidityAddition:
    lending_pool_adapter: "FolksLendingPoolAdapter"
    primary_asset_amount: int
    secondary_asset_amount: int
    liquidity_addition: LiquidityAddition = dataclasses.field(init=False)

    def __post_init__(self):
        self.liquidity_addition = LiquidityAddition(
            pool=self.lending_pool_adapter.pact_pool,
            primary_asset_amount=self.lending_pool_adapter.primary_lending_pool.convert_deposit(
                self.primary_asset_amount
            ),
            secondary_asset_amount=self.lending_pool_adapter.secondary_lending_pool.convert_deposit(
                self.secondary_asset_amount
            ),
        )
        self.liquidity_addition.effect.tx_fee = PRE_ADD_LIQ_FEE + ADD_LIQ_FEE


@dataclasses.dataclass
class FolksLendingPoolAdapter:
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
    ) -> LendingLiquidityAddition:
        return LendingLiquidityAddition(
            lending_pool_adapter=self,
            primary_asset_amount=primary_asset_amount,
            secondary_asset_amount=secondary_asset_amount,
        )

    def prepare_add_liquidity_tx_group(
        self,
        address: str,
        liquidity_addition: LendingLiquidityAddition,
    ) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_add_liquidity_txs(
            address, liquidity_addition.liquidity_addition, suggested_params
        )
        return TransactionGroup(txs)

    def build_add_liquidity_txs(
        self,
        address: str,
        liquidity_addition: LiquidityAddition,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[algosdk.transaction.Transaction]:
        deposit_primary_tx = self.primary_lending_pool.original_asset.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=liquidity_addition.primary_asset_amount,
            suggested_params=suggested_params,
        )

        deposit_secondary_tx = (
            self.secondary_lending_pool.original_asset.build_transfer_tx(
                sender=address,
                receiver=self.escrow_address,
                amount=liquidity_addition.secondary_asset_amount,
                suggested_params=suggested_params,
            )
        )

        pre_add_liq_tx = algosdk.transaction.ApplicationNoOpTxn(
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

        add_liq_tx = algosdk.transaction.ApplicationNoOpTxn(
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

        return [
            deposit_primary_tx,
            deposit_secondary_tx,
            pre_add_liq_tx,
            add_liq_tx,
        ]

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
    ) -> Swap:
        f_asset = self.original_asset_to_f_asset(asset)

        if asset == self.primary_lending_pool.original_asset:
            deposited_lending_pool = self.primary_lending_pool
            received_lending_pool = self.secondary_lending_pool
        else:
            deposited_lending_pool = self.secondary_lending_pool
            received_lending_pool = self.primary_lending_pool

        f_amount = deposited_lending_pool.convert_deposit(amount)

        swap = self.pact_pool.prepare_swap(
            f_asset, f_amount, slippage_pct, swap_for_exact
        )
        swap.asset_deposited = self.f_asset_to_original_asset(swap.asset_deposited)
        swap.asset_received = self.f_asset_to_original_asset(swap.asset_received)

        swap.effect.amount_deposited = amount
        swap.effect.amount_received = received_lending_pool.convert_withdraw(
            swap.effect.amount_received
        )

        return swap

    def prepare_swap_tx_group(self, swap: Swap, address: str) -> TransactionGroup:
        suggested_params = self.algod.suggested_params()
        txs = self.build_swap_txs(swap, address, suggested_params)
        return TransactionGroup(txs)

    def build_swap_txs(
        self,
        swap: Swap,
        address: str,
        suggested_params: algosdk.transaction.SuggestedParams,
    ) -> list[algosdk.transaction.Transaction]:
        deposit_tx = swap.asset_deposited.build_transfer_tx(
            sender=address,
            receiver=self.escrow_address,
            amount=swap.amount,
            suggested_params=suggested_params,
        )

        swap_tx = algosdk.transaction.ApplicationNoOpTxn(
            sender=address,
            sp=sp_fee(suggested_params, SWAP_FEE),
            index=self.app_id,
            app_args=[
                SWAP_SIG,
                *[ABI_BYTE.encode(v) for v in [0, 1, 2, 3]],  # assets
                *[ABI_BYTE.encode(v) for v in [1, 2, 3, 4]],  # apps
                swap.effect.minimum_amount_received,
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

        return [deposit_tx, swap_tx]

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
        assert 0 < len(asset_ids) < 8

        asset_ids = [asset_id for asset_id in asset_ids if asset_id > 0]

        payment_tx = algosdk.transaction.PaymentTxn(
            sender=address,
            receiver=self.escrow_address,
            amt=len(asset_ids) * 100_000,
            sp=suggested_params,
        )

        opt_in_tx = algosdk.transaction.ApplicationNoOpTxn(
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

        return [payment_tx, opt_in_tx]
