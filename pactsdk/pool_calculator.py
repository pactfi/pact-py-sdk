import math
from decimal import Decimal as D
from typing import TYPE_CHECKING

from .asset import Asset

if TYPE_CHECKING:
    from .pool import Pool


class PoolCalculator:
    def __init__(self, pool: "Pool"):
        self.pool = pool

    @property
    def primary_asset_amount(self):
        return D(self.pool.internal_state.A)

    @property
    def secondary_asset_amount(self):
        return D(self.pool.internal_state.B)

    @property
    def is_empty(self):
        return (
            self.primary_asset_amount.is_zero() or self.secondary_asset_amount.is_zero()
        )

    @property
    def primary_asset_price(self):
        if self.is_empty:
            return D(0)

        return self.get_primary_asset_price(
            self.primary_asset_amount,
            self.secondary_asset_amount,
        )

    @property
    def secondary_asset_price(self):
        if self.is_empty:
            return D(0)

        return self.get_secondary_asset_price(
            self.primary_asset_amount,
            self.secondary_asset_amount,
        )

    def get_primary_asset_price(
        self, primary_liq_amount: D, secondary_liq_amount: D
    ) -> D:
        if primary_liq_amount.is_zero() or secondary_liq_amount.is_zero():
            return D(0)

        return (secondary_liq_amount / self.pool.secondary_asset.ratio) / (
            primary_liq_amount / self.pool.primary_asset.ratio
        )

    def get_secondary_asset_price(
        self,
        primary_liq_amount: D,
        secondary_liq_amount: D,
    ) -> D:
        if primary_liq_amount.is_zero() or secondary_liq_amount.is_zero():
            return D(0)

        return (primary_liq_amount / self.pool.primary_asset.ratio) / (
            secondary_liq_amount / self.pool.secondary_asset.ratio
        )

    def get_minimum_amount_in(
        self, asset: Asset, amount: int, slippage_pct: float
    ) -> int:
        amount_in = self.get_net_amount_in(asset, amount)
        return math.floor(amount_in - (amount_in * (D(slippage_pct) / 100)))

    def get_gross_amount_in(self, asset: Asset, amount: int) -> int:
        if asset == self.pool.primary_asset:
            return self._swap_primary_gross_amount(amount)

        return self._swap_secondary_gross_amount(amount)

    def get_net_amount_in(self, asset: Asset, amount: int) -> int:
        gross_amount = self.get_gross_amount_in(asset, amount)
        return self._subtract_fee(gross_amount)

    def get_fee(self, asset: Asset, amount: int) -> int:
        return self.get_gross_amount_in(asset, amount) - (
            self.get_net_amount_in(asset, amount)
        )

    def get_asset_price_after_liq_change(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> D:
        new_primary_liq = self.primary_asset_amount + primary_liq_change
        new_secondary_liq = self.secondary_asset_amount + secondary_liq_change
        if asset == self.pool.primary_asset:
            return self.get_primary_asset_price(new_primary_liq, new_secondary_liq)
        return self.get_secondary_asset_price(new_primary_liq, new_secondary_liq)

    def get_price_change_pct(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> D:
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

    def get_swap_price(self, asset_out: Asset, amount_out: int) -> D:
        asset_in = self.pool.get_other_asset(asset_out)
        amount_in = self.get_gross_amount_in(asset_out, amount_out)
        diff_ratio = D(asset_out.ratio / asset_in.ratio)
        return amount_in / D(amount_out) * diff_ratio

    def _subtract_fee(self, asset_gross_amount: int) -> int:
        return int(asset_gross_amount * (10000 - self.pool.fee_bps) / D(10000))

    def _swap_primary_gross_amount(self, amount: int) -> int:
        return int(
            amount
            * (self.secondary_asset_amount)
            / D(self.primary_asset_amount + amount)
        )

    def _swap_secondary_gross_amount(self, amount: int) -> int:
        return int(
            amount
            * (self.primary_asset_amount)
            / D(self.secondary_asset_amount + amount)
        )
