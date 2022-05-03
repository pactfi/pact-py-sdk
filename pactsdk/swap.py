"""Set of utility classes for managing performing swaps.
 

"""
from dataclasses import dataclass
from decimal import Decimal as D
from typing import TYPE_CHECKING

from .asset import Asset
from .transaction_group import TransactionGroup

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class SwapEffect:
    """A data class containing the relevant information about the outcome of a swap.

    The swap effect is created from the main `Swap` class, accessible from the effect function.
    See the build_effect description for how the values are precisely calculated.
    """

    amount_in: int
    """The amount deposited in the swap."""
    amount_out: int
    """The amount received from the swap."""
    minimum_amount_in: int
    """The minimal amount that will be required to be a valid swap."""
    fee: int
    """The fee in micro algo for the transaction."""
    primary_asset_price_after_swap: D
    """The total quantity of primary asset in the pool after the swap has been committed."""
    secondary_asset_price_after_swap: D
    """The total quantity of secondary asset in the pool after the swap has been committed."""
    primary_asset_price_change_pct: D
    """The percentage change of the primary asset."""
    secondary_asset_price_change_pct: D
    """The percentage change of the secondary asset."""
    price: D
    """The implied price for the swap."""


@dataclass
class Swap:
    """Represents a swap out of an amount of an asset from a pool with a maximum slippage percentage.

    This is a data class that represents a swap on a give pool.
    """

    pool: "Pool"
    """The pool that the swap is being performed in."""
    asset_out: Asset
    """The asset being received from the swap."""
    amount_out: int
    """The amount of asset to receive"""
    slippage_pct: float
    """The maximum amount of slippage in percent terms to tollerate."""

    def __post_init__(self):
        """Initialized derived values: the asset in and the effect of the swap.

        The asset_in is set to the opposite asset to the asset_out in the pool.
        The effect is set to the values implied by the swap. See the validate_swap function for more details.

        The initialize will also validate that the swap and raise a value error.
        """
        self.asset_in = self.pool.get_other_asset(self.asset_out)
        self.validate_swap()
        self.effect = self._build_effect()

    def prepare_tx(self, address: str) -> TransactionGroup:
        """Creates a signed transaction for swapping out the asset.

        Args:
            address (str): The private key to sign the transactions with.

        Returns:
            TransactionGroup: Transaction group to produce a swap.
        """
        return self.pool.prepare_swap_tx(self, address)

    def validate_swap(self):
        """Validates that the swap details are valid.

        Specifically this validates that the slippage percentage is correct between 0 - 100 and the pool
        is not empty.

        Raises:
            ValueError: Raised when the slippage is below 0 or above 100.
            ValueError: Raised when the pool is empty, has no tokens.
        """
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
