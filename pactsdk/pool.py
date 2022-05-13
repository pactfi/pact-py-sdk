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
    assert pact_api_url
    encoded_params = urlencode(params)
    response = requests.get(f"{pact_api_url}/api/pools?{encoded_params}")
    return response.json()


def fetch_app_global_state(
    algod: AlgodClient,
    app_id: int,
) -> AppInternalState:
    app_info = algod.application_info(app_id)
    return parse_global_pool_state(app_info["params"]["global-state"])


def fetch_pool_by_id(algod: AlgodClient, app_id: int):
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
    data = list_pools(
        pact_api_url,
        primary_asset__algoid=primary_asset_index,
        secondary_asset__algoid=secondary_asset_index,
    )
    return [int(pool["appid"]) for pool in data["results"]]


@dataclass
class Pool:
    algod: AlgodClient
    app_id: int
    primary_asset: Asset
    secondary_asset: Asset
    liquidity_asset: Asset
    internal_state: AppInternalState
    fee_bps: int = 30

    def __post_init__(self):
        self.calculator = PoolCalculator(self)
        self.state = self.parse_internal_state(self.internal_state)

    def get_escrow_address(self):
        return algosdk.logic.get_application_address(self.app_id)

    def get_other_asset(self, asset: Asset) -> Asset:
        if asset == self.primary_asset:
            return self.secondary_asset

        if asset == self.secondary_asset:
            return self.primary_asset

        raise PactSdkError(f"Asset with index {asset.index} is not a pool asset.")

    def update_state(self) -> PoolState:
        self.internal_state = fetch_app_global_state(self.algod, self.app_id)
        self.state = self.parse_internal_state(self.internal_state)
        return self.state

    def prepare_add_liquidity_tx_group(
        self,
        address: str,
        primary_asset_amount: int,
        secondary_asset_amount: int,
    ):
        suggested_params = self.algod.suggested_params()
        txs = self.build_add_liquidity_txs(
            address, primary_asset_amount, secondary_asset_amount, suggested_params
        )
        return TransactionGroup(txs)

    def build_add_liquidity_txs(
        self,
        address: str,
        primary_asset_amount: int,
        secondary_asset_amount: int,
        suggested_params: transaction.SuggestedParams,
        note=b"",
    ):
        txs: list[transaction.Transaction] = []
        if self.calculator.is_empty:
            # Adding initial liquidity has a limitation that the product of 2 assets must be lower then 2**64. Let's check if we can fit below the limit.
            max_product = 2**64
            product = primary_asset_amount * secondary_asset_amount
            if product >= max_product:
                # Need to split the liquidity into two chunks.
                divisor = int((product / max_product) ** 0.5 + 1)
                primary_small_amount = primary_asset_amount // divisor
                secondary_small_amount = secondary_asset_amount // divisor

                primary_asset_amount -= primary_small_amount
                secondary_asset_amount -= secondary_small_amount

                txs = self.build_add_liquidity_txs(
                    address=address,
                    primary_asset_amount=primary_small_amount,
                    secondary_asset_amount=secondary_small_amount,
                    suggested_params=suggested_params,
                    note=b"Initial add liquidity",
                )

        tx1 = self._make_deposit_tx(
            address=address,
            asset=self.primary_asset,
            amount=primary_asset_amount,
            suggested_params=suggested_params,
        )
        tx2 = self._make_deposit_tx(
            address=address,
            asset=self.secondary_asset,
            amount=secondary_asset_amount,
            suggested_params=suggested_params,
        )
        tx3 = self._make_application_noop_tx(
            address=address,
            fee=3000,
            args=["ADDLIQ", 0],
            extraAsset=self.liquidity_asset,
            suggested_params=suggested_params,
            note=note,
        )

        return [*txs, tx1, tx2, tx3]

    def prepare_remove_liquidity_tx_group(self, address: str, amount: int):
        suggested_params = self.algod.suggested_params()
        txs = self.build_remove_liquidity_txs(address, amount, suggested_params)
        return TransactionGroup(txs)

    def build_remove_liquidity_txs(
        self, address: str, amount: int, suggested_params: transaction.SuggestedParams
    ):
        tx1 = self._make_deposit_tx(
            address=address,
            amount=amount,
            asset=self.liquidity_asset,
            suggested_params=suggested_params,
        )
        tx2 = self._make_application_noop_tx(
            address=address,
            fee=3000,
            args=["REMLIQ", 0, 0],  # min expected primary, min expected secondary
            suggested_params=suggested_params,
        )

        return [tx1, tx2]

    def prepare_swap(self, asset: Asset, amount: int, slippage_pct: float) -> Swap:
        assert self.is_asset_in_the_pool(asset), f"Asset {asset.index} not in the pool"
        return Swap(
            self,
            asset_deposited=asset,
            amount_deposited=amount,
            slippage_pct=slippage_pct,
        )

    def prepare_swap_tx_group(self, swap: Swap, address: str):
        suggested_params = self.algod.suggested_params()
        txs = self.build_swap_txs(swap, address, suggested_params)
        return TransactionGroup(txs)

    def build_swap_txs(
        self, swap: Swap, address: str, suggested_params: transaction.SuggestedParams
    ):
        tx1 = self._make_deposit_tx(
            address=address,
            amount=swap.amount_deposited,
            asset=swap.asset_deposited,
            suggested_params=suggested_params,
        )
        tx2 = self._make_application_noop_tx(
            address=address,
            fee=2000,
            args=["SWAP", swap.effect.minimum_amount_received],
            suggested_params=suggested_params,
        )

        return [tx1, tx2]

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
