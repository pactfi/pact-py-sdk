import math
from typing import TYPE_CHECKING, Protocol

from pactsdk.constant_product_calculator import ConstantProductCalculator
from pactsdk.exceptions import PactSdkError
from pactsdk.stableswap_calculator import StableswapCalculator

from .asset import Asset

if TYPE_CHECKING:
    from .pool import Pool


class SwapCalculator(Protocol):
    pool: "Pool"

    def get_price(self, liq_a: float, liq_b: float) -> float:
        ...

    # For the following two methods:
    # liq_a - primary liquidity if swapping primary asset, secondary otherwise
    # liq_b - vice versa
    def get_swap_gross_amount_received(
        self,
        liq_a: int,
        liq_b: int,
        amount_deposited: int,
    ) -> int:
        ...

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        amount_received: int,
    ) -> int:
        ...


class PoolCalculator:
    def __init__(self, pool: "Pool"):
        self.pool = pool

        self.swap_calculator: SwapCalculator
        if pool.pool_type == "CONSTANT_PRODUCT":
            self.swap_calculator = ConstantProductCalculator(pool)
        elif pool.pool_type == "STABLESWAP":
            self.swap_calculator = StableswapCalculator(pool)
        else:
            raise PactSdkError(f"Unknown pool type: ${pool.pool_type}")

    @property
    def primary_asset_amount(self):
        return self.pool.internal_state.A

    @property
    def secondary_asset_amount(self):
        return self.pool.internal_state.B

    @property
    def primary_asset_amount_decimal(self):
        return self.pool.internal_state.A / self.pool.primary_asset.ratio

    @property
    def secondary_asset_amount_decimal(self):
        return self.pool.internal_state.B / self.pool.secondary_asset.ratio

    @property
    def is_empty(self):
        return self.primary_asset_amount == 0 or self.secondary_asset_amount == 0

    @property
    def primary_asset_price(self):
        return self.swap_calculator.get_price(
            self.primary_asset_amount_decimal, self.secondary_asset_amount_decimal
        )

    @property
    def secondary_asset_price(self):
        return self.swap_calculator.get_price(
            self.secondary_asset_amount_decimal,
            self.primary_asset_amount_decimal,
        )

    def amount_deposited_to_net_amount_received(
        self, asset: Asset, amount_deposited: int
    ) -> int:
        gross_amount_received = self.amount_deposited_to_gross_amount_received(
            asset, amount_deposited
        )
        fee = self.get_fee_from_gross_amount(gross_amount_received)
        return gross_amount_received - fee

    def net_amount_received_to_amount_deposited(
        self, asset: Asset, net_amount_received: int
    ) -> int:
        fee = self.get_fee_from_net_amount(net_amount_received)
        net_amount_received += fee
        return self.gross_amount_received_to_amount_deposited(
            asset, net_amount_received
        )

    def get_fee_from_gross_amount(self, gross_amount: int) -> int:
        return gross_amount - (gross_amount * (10_000 - self.pool.fee_bps)) // 10_000

    def get_fee_from_net_amount(self, net_amount: int) -> int:
        return math.ceil(
            net_amount / ((10_000 - self.pool.fee_bps) / 10_000) - net_amount
        )

    def gross_amount_received_to_amount_deposited(
        self,
        asset: Asset,
        int_gross_amount_received: int,
    ) -> int:
        A, B = self.get_liquidities(asset)
        return self.swap_calculator.get_swap_amount_deposited(
            A,
            B,
            int_gross_amount_received,
        )

    def amount_deposited_to_gross_amount_received(
        self,
        asset: Asset,
        amount_deposited: int,
    ) -> int:
        A, B = self.get_liquidities(asset)
        return self.swap_calculator.get_swap_gross_amount_received(
            A,
            B,
            amount_deposited,
        )

    def get_liquidities(self, asset: Asset) -> tuple[int, int]:
        A, B = [self.primary_asset_amount, self.secondary_asset_amount]
        if asset != self.pool.primary_asset:
            A, B = B, A
        return A, B

    def get_minimum_amount_received(
        self, asset: Asset, amount: int, slippage_pct: float
    ) -> int:
        amount_received = self.amount_deposited_to_net_amount_received(asset, amount)
        return math.floor(amount_received - (amount_received * (slippage_pct / 100)))

    def get_fee(self, asset: Asset, amount_deposited: int) -> int:
        return self.amount_deposited_to_gross_amount_received(
            asset, amount_deposited
        ) - (self.amount_deposited_to_net_amount_received(asset, amount_deposited))

    def get_asset_price_after_liq_change(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> float:
        new_primary_liq = (
            self.primary_asset_amount + primary_liq_change
        ) / self.pool.primary_asset.ratio
        new_secondary_liq = (
            self.secondary_asset_amount + secondary_liq_change
        ) / self.pool.secondary_asset.ratio

        if asset == self.pool.primary_asset:
            return self.swap_calculator.get_price(new_primary_liq, new_secondary_liq)
        return self.swap_calculator.get_price(new_secondary_liq, new_primary_liq)

    def get_price_change_pct(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> float:
        old_price = (
            self.primary_asset_price
            if asset == self.pool.primary_asset
            else self.secondary_asset_price
        )
        new_price = self.get_asset_price_after_liq_change(
            asset,
            primary_liq_change,
            secondary_liq_change,
        )
        return new_price / old_price * 100 - 100

    def get_swap_price(self, asset_deposited: Asset, amount_deposited: int) -> float:
        asset_received = self.pool.get_other_asset(asset_deposited)
        amount_received = self.amount_deposited_to_gross_amount_received(
            asset_deposited, amount_deposited
        )
        diff_ratio = asset_deposited.ratio / asset_received.ratio
        return amount_received / amount_deposited * diff_ratio
