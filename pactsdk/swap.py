"""Set of utility classes for managing and performing swaps.
"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pactsdk.stableswap_calculator import StableswapCalculator, get_tx_fee

from .asset import Asset
from .transaction_group import TransactionGroup

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class SwapEffect:
    """Swap Effect are the basic details of the effect on the pool of performing the swap."""

    amount_received: int
    amount_deposited: int
    minimum_amount_received: int
    fee: int
    primary_asset_price_after_swap: float
    secondary_asset_price_after_swap: float
    primary_asset_price_change_pct: float
    secondary_asset_price_change_pct: float
    price: float
    tx_fee: int

    amplifier: float
    """Stableswap only. Zero otherwise."""


@dataclass
class Swap:
    """Swap class represents a swap trade on a particular pool.

    Typically, users don't have to manually instantiate this class. Use :py:meth:`pactsdk.pool.Pool.prepare_swap` instead.
    """

    pool: "Pool"
    """The pool the swap is going to be performed in."""

    asset_deposited: Asset
    """The asset that will be swapped (deposited in the contract)."""

    asset_received: Asset = field(init=False)
    """The asset that will be received."""

    amount: int
    """Either the amount to swap (deposit) or the amount to receive depending on the `swap_for_exact` parameter."""

    slippage_pct: float
    """The maximum percentage of slippage allowed in performing the swap."""

    swap_for_exact: bool = False
    """If `true` then `amount` is what you want to receive from the swap. Otherwise, it's an amount that you want to swap (deposit). Note that the contracts do not support the "swap exact for" swap. It works by calculating the amount to deposit on the client side and doing a normal swap on the exchange."""

    effect: SwapEffect = field(init=False)
    """The effect of the swap computed at the time of construction."""

    def __post_init__(self):
        self.asset_received = self.pool.get_other_asset(self.asset_deposited)
        self._validate_swap()
        self.effect = self._build_effect()

    def prepare_tx_group(self, address: str) -> TransactionGroup:
        """Creates the transactions needed to perform the swap trade and returns them as a transaction group ready to be signed and committed.

        Args:
            address: The account that will be performing the swap.

        Returns:
            A transaction group that when executed will perform the swap.
        """
        return self.pool.prepare_swap_tx_group(self, address)

    def _validate_swap(self):
        if self.slippage_pct < 0 or self.slippage_pct > 100:
            raise ValueError("Splippage must be between 0 and 100")

        if self.pool.calculator.is_empty:
            raise ValueError("Pool is empty and swaps are impossible.")

    def _build_effect(self) -> SwapEffect:
        if self.swap_for_exact:
            amount_received = self.amount
            amount_deposited = (
                self.pool.calculator.net_amount_received_to_amount_deposited(
                    self.asset_deposited, self.amount
                )
            )
        else:
            amount_received = (
                self.pool.calculator.amount_deposited_to_net_amount_received(
                    self.asset_deposited, self.amount
                )
            )
            amount_deposited = self.amount

        if self.asset_deposited == self.pool.primary_asset:
            primary_liq_change = amount_deposited
            secondary_liq_change = -amount_received
        else:
            primary_liq_change = -amount_received
            secondary_liq_change = amount_deposited

        amplifier = 0
        tx_fee = 2000
        swap_calc = self.pool.calculator.swap_calculator

        if isinstance(swap_calc, StableswapCalculator):
            amplifier = swap_calc.get_amplifier() / (
                self.pool.internal_state.PRECISION or 1
            )
            tx_fee = get_tx_fee(swap_calc.swap_invariant_iterations, 1)

        return SwapEffect(
            amount_deposited=amount_deposited,
            amount_received=amount_received,
            minimum_amount_received=self.pool.calculator.get_minimum_amount_received(
                self.asset_deposited, amount_deposited, self.slippage_pct
            ),
            price=self.pool.calculator.get_swap_price(
                self.asset_deposited, amount_deposited
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
            primary_asset_price_change_pct=self.pool.calculator.get_price_impact_pct(
                self.pool.primary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            secondary_asset_price_change_pct=self.pool.calculator.get_price_impact_pct(
                self.pool.secondary_asset,
                primary_liq_change,
                secondary_liq_change,
            ),
            fee=self.pool.calculator.get_fee(self.asset_deposited, amount_deposited),
            amplifier=amplifier,
            tx_fee=tx_fee,
        )
