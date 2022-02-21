import base64
import copy
from dataclasses import dataclass
from decimal import Decimal as D
from typing import Any, Optional
from urllib.parse import urlencode

import algosdk
import requests
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

from .asset import Asset, fetch_asset_by_index
from .exceptions import PactSdkError
from .pool_calculator import PoolCalculator
from .swap import Swap
from .transaction_group import TransactionGroup


@dataclass
class AppInternalState:
    L: int
    A: int
    B: int
    LTID: int

    # None to make backward compatible. Old contracts don't have the config.
    CONFIG: Any = None


@dataclass
class PoolState:
    total_liquidity: int
    total_primary: int
    total_secondary: int
    primary_asset_price: D
    secondary_asset_price: D


def list_pools(pact_api_url: str, **params):
    assert pact_api_url
    encoded_params = urlencode(params)
    response = requests.get(f"{pact_api_url}/api/pools?{encoded_params}")
    return response.json()


def fetch_app_state(
    algod: AlgodClient,
    app_id: int,
) -> AppInternalState:
    app_info = algod.application_info(app_id)
    state_dict = parse_global_state(app_info["params"]["global-state"])
    return AppInternalState(**state_dict)


def parse_global_state(kv: list) -> dict[str, int]:
    # Transform algorand key-value schema into python dict with key value pairs
    res = {}
    for elem in kv:
        key = str(base64.b64decode(elem["key"]), encoding="ascii")
        if elem["value"]["type"] == 1:
            val = elem["value"]["bytes"]
        else:
            val = elem["value"]["uint"]
        res[key] = val
    return res


def fetch_pool(
    algod: AlgodClient,
    asset_a: Asset,
    asset_b: Asset,
    app_id: int = 0,
    fee_bps: int = 30,
    pact_api_url="",
) -> "Pool":
    # Make sure that the user didn't mess up assets order.
    # Primary asset always has lower index.
    primary_asset, secondary_asset = sorted([asset_a, asset_b], key=lambda a: a.index)

    if not app_id:
        assert pact_api_url, "Must provide pactifyApiUrl or app_id."

        app_id = get_app_id_from_assets(
            pact_api_url,
            primary_asset,
            secondary_asset,
        )
        if not app_id:
            raise PactSdkError(
                f"Cannot find pool for assets {primary_asset.index} and {secondary_asset.index}.",
            )

    app_state = fetch_app_state(algod, app_id)
    liquidity_asset = fetch_asset_by_index(algod, app_state.LTID)

    return Pool(
        algod=algod,
        app_id=app_id,
        primary_asset=primary_asset,
        secondary_asset=secondary_asset,
        liquidity_asset=liquidity_asset,
        internal_state=app_state,
        fee_bps=fee_bps,
    )


def get_app_id_from_assets(
    pact_api_url: str,
    primary_asset: Asset,
    secondary_asset: Asset,
) -> int:
    data = list_pools(
        pact_api_url,
        primary_asset__algoid=primary_asset.index,
        secondary_asset__algoid=secondary_asset.index,
    )
    if data["results"]:
        return data["results"][0]["appid"]
    return 0


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
        self.internal_state = fetch_app_state(self.algod, self.app_id)
        self.state = self.parse_internal_state(self.internal_state)
        return self.state

    def prepare_add_liquidity_tx(
        self,
        address: str,
        primary_asset_amount: int,
        secondary_asset_amount: int,
    ):
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
