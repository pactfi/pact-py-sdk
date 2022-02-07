from dataclasses import dataclass
from decimal import Decimal as D
from typing import TYPE_CHECKING

from .asset import Asset
from .transaction_group import TransactionGroup

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class SwapEffect:
    amount_in: int
    amount_out: int
    minimum_amount_in: int
    fee: int
    primary_asset_price_after_swap: D
    secondary_asset_price_after_swap: D
    primary_asset_price_change_pct: D
    secondary_asset_price_change_pct: D
    price: D


@dataclass
class Swap:
    pool: "Pool"
    asset_out: Asset
    amount_out: int
    slippage_pct: float

    def __post_init__(self):
        self.asset_in = self.pool.get_other_asset(self.asset_out)
        self.validate_swap()
        self.effect = self._build_effect()

    def prepare_tx(self, address: str) -> TransactionGroup:
        return self.pool.prepare_swap_tx(self, address)

    def validate_swap(self):
        if self.slippage_pct < 0 or self.slippage_pct > 100:
            raise ValueError("Splippage must be between 0 and 100")

        if self.pool.calculator.is_empty:
            raise ValueError("Pool is empty and swaps are impossible.")

    def _build_effect(self) -> SwapEffect:
        amount_in = self.pool.calculator.get_net_amount_in(
            self.asset_out, self.amount_out
        )

        if self.asset_out == self.pool.primary_asset:
            primary_liq_change = self.amount_out
            secondary_liq_change = -amount_in
        else:
            primary_liq_change = -amount_in
            secondary_liq_change = self.amount_out

        return SwapEffect(
            amount_out=self.amount_out,
            amount_in=amount_in,
            minimum_amount_in=self.pool.calculator.get_minimum_amount_in(
                self.asset_out, self.amount_out, self.slippage_pct
            ),
            price=self.pool.calculator.get_swap_price(self.asset_out, self.amount_out),
            primary_asset_price_after_swap=self.pool.calculator.get_asset_price_after_liq_change(
                self.pool.primary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            secondary_asset_price_after_swap=self.pool.calculator.get_asset_price_after_liq_change(
                self.pool.secondary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            primary_asset_price_change_pct=self.pool.calculator.get_price_change_pct(
                self.pool.primary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            secondary_asset_price_change_pct=self.pool.calculator.get_price_change_pct(
                self.pool.secondary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            fee=self.pool.calculator.get_fee(self.asset_out, self.amount_out),
        )
