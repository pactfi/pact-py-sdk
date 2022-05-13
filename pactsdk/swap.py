from dataclasses import dataclass
from decimal import Decimal as D
from typing import TYPE_CHECKING

from .asset import Asset
from .transaction_group import TransactionGroup

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class SwapEffect:
    amount_received: int
    amount_deposited: int
    minimum_amount_received: int
    fee: int
    primary_asset_price_after_swap: D
    secondary_asset_price_after_swap: D
    primary_asset_price_change_pct: D
    secondary_asset_price_change_pct: D
    price: D


@dataclass
class Swap:
    pool: "Pool"
    asset_deposited: Asset
    amount_deposited: int
    slippage_pct: float

    def __post_init__(self):
        self.asset_in = self.pool.get_other_asset(self.asset_deposited)
        self.validate_swap()
        self.effect = self._build_effect()

    def prepare_tx_group(self, address: str) -> TransactionGroup:
        return self.pool.prepare_swap_tx_group(self, address)

    def validate_swap(self):
        if self.slippage_pct < 0 or self.slippage_pct > 100:
            raise ValueError("Splippage must be between 0 and 100")

        if self.pool.calculator.is_empty:
            raise ValueError("Pool is empty and swaps are impossible.")

    def _build_effect(self) -> SwapEffect:
        amount_received = self.pool.calculator.get_net_amount_received(
            self.asset_deposited, self.amount_deposited
        )

        if self.asset_deposited == self.pool.primary_asset:
            primary_liq_change = self.amount_deposited
            secondary_liq_change = -amount_received
        else:
            primary_liq_change = -amount_received
            secondary_liq_change = self.amount_deposited

        return SwapEffect(
            amount_deposited=self.amount_deposited,
            amount_received=amount_received,
            minimum_amount_received=self.pool.calculator.get_minimum_amount_received(
                self.asset_deposited, self.amount_deposited, self.slippage_pct
            ),
            price=self.pool.calculator.get_swap_price(
                self.asset_deposited, self.amount_deposited
            ),
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
            fee=self.pool.calculator.get_fee(
                self.asset_deposited, self.amount_deposited
            ),
        )
