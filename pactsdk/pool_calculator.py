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
        """The amount of the primary asset in the pool"""
        return D(self.pool.internal_state.A)

    @property
    def secondary_asset_amount(self):
        """The amount of the secondary asset in the pool"""
        return D(self.pool.internal_state.B)

    @property
    def is_empty(self):
        """True if the primary and secondary asset amounts are zero"""
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
        """The price of the primary asset.

        The price is the amount of the secondary asset you get for a single unit of primary asset.
        The price will be zero if either the primary or secondary amount is zero.
        If it is not zero, the price is the secondary value divided by the primary value.
        The value is the amount of base units divided by the assets ratio.

        Args:
            primary_liq_amount: the number of primary asset base units for price calculation.
            secondary_liq_amount: the number of secondary asset base units for price calculation.

        Returns:
            A decimal representing the amount of secondary asset for a unit of the primary asset.

        """
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
        """The price of the secondary asset.

        The secondary price is the value of primary asset for a single unit of secondary asset.
        The price will be zero if either the primary or secondary amount passed in is zero.
        If it is not zero, the price is the primary value divided by the secondary value.
        Where the value is calculated by dividing the base units by the asset ratio.

        Args:
            primary_liq_amount: The number of primary asset base units to calculate the price for.
            secondary_liq_amount: The number of secondary asset base units to calculate the price for.

        Returns:
            A decimal representing the amount of primary asset for a unity of secondary asset.
        """
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
        """The amount in minus any fees.

        This is the gross amount in minus the fee charge for the pool.

        """
        gross_amount = self.get_gross_amount_in(asset, amount)
        return self._subtract_fee(gross_amount)

    def get_fee(self, asset: Asset, amount: int) -> int:
        """Fee on asset deposited."""
        return self.get_gross_amount_in(asset, amount) - (
            self.get_net_amount_in(asset, amount)
        )

    def get_asset_price_after_liq_change(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> D:
        """The price of the asset after the change of primary and secondary liquidity.

        This is a what-if calculation that determines the price if the liquidity of the
        primary and secondary asset was changed by the amount passed in.
        The price is expressed in terms of the Asset. The Assetmust be the primary or secondary asset.

        Args:
            asset: The asset to calculate the price based on.
            primary_liq_change: the base units to change the primary liquidity by.
            secondary_liq_change: the base units to change the secondary liquidity by.

        Returns:
            The price of the asset if the liquidity was changed as per the arguments.
        """
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
        """The gross amount minus the basis points fee. Note the amount is floored"""
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
