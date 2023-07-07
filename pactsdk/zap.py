"""Set of utility classes for managing and performing zaps.
"""
import copy
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .add_liquidity import LiquidityAddition
from .asset import Asset
from .swap import Swap
from .transaction_group import TransactionGroup

if TYPE_CHECKING:
    from .pool import Pool


FEE_PRECISION = 10**4


@dataclass
class ZapParams:
    """All amounts that should be used in swap and add liquidity transactions."""

    swap_deposited: int
    primary_add_liq: int
    secondary_add_liq: int


def get_constant_product_zap_params(
    liq_a: int,
    liq_b: int,
    zap_amount: int,
    fee_bps: int,
    pact_fee_bps: int,
) -> ZapParams:
    swap_deposited = get_swap_amount_deposited_from_zapping(
        zap_amount, liq_a, fee_bps, pact_fee_bps
    )
    primary_add_liq = zap_amount - swap_deposited
    secondary_add_liq = get_secondary_added_liquidity_from_zapping(
        swap_deposited, liq_a, liq_b, fee_bps
    )
    return ZapParams(swap_deposited, primary_add_liq, secondary_add_liq)


def get_swap_amount_deposited_from_zapping(
    zap_amount: int,
    total_amount: int,
    fee_bps: int,
    pact_fee_bps: int,
) -> int:
    pool_fee = fee_bps - pact_fee_bps
    a = (-FEE_PRECISION - pool_fee + fee_bps) // FEE_PRECISION
    b = (
        -2 * total_amount * FEE_PRECISION
        + zap_amount * pool_fee
        + total_amount * fee_bps
    ) // FEE_PRECISION
    c = total_amount * zap_amount

    delta = b * b - 4 * a * c
    if b < 0:
        result = (-b - math.isqrt(delta)) // (2 * a)
    else:
        result = (2 * c) // (-b + math.isqrt(delta))
    return result


def get_secondary_added_liquidity_from_zapping(
    swap_deposited: int,
    total_primary: int,
    total_secondary: int,
    fee_bps,
) -> int:
    return (swap_deposited * total_secondary * (FEE_PRECISION - fee_bps)) // (
        (total_primary + swap_deposited) * FEE_PRECISION
    )


@dataclass
class Zap:
    """Zap class represents a zap trade on a particular pool, which allows to exchange single asset for PLP token.

    Zap performs a swap to get second asset from the pool and then adds liquidity using both of those assets. Users may be left with some leftovers due to rounding and slippage settings.

    Zaps are meant only for Constant Product pools; For Stableswaps, adding only one asset works out of the box.

    Typically, users don't have to manually instantiate this class. Use :py:meth:`pactsdk.pool.Pool.prepare_zap` instead.
    """

    pool: "Pool"
    """The pool the zap is going to be performed in."""

    asset: Asset
    """The asset that will be used in zap."""

    amount: int
    """Amount to be used in zap."""

    slippage_pct: float
    """The maximum amount of slippage allowed in performing the swap."""

    swap: Swap = field(init=False)
    """The swap object that will be executed during the zap."""

    liquidity_addition: LiquidityAddition = field(init=False)
    """Liquidity Addition object that will be executed during the zap."""

    params: ZapParams = field(init=False)
    """All amounts used in swap and add liquidity transactions."""

    def __post_init__(self):
        if not self.pool.is_asset_in_the_pool(self.asset):
            raise AssertionError("Provided asset was not found in the pool.")

        if self.pool.pool_type == "STABLESWAP":
            raise AssertionError("Zap can only be made on constant product pools.")

        self.params = self.get_zap_params()
        self.swap = self.pool.prepare_swap(
            self.asset, self.params.swap_deposited, self.slippage_pct
        )
        self.liquidity_addition = self.prepare_add_liq()

    def prepare_tx_group(self, address: str) -> TransactionGroup:
        """Creates the transactions needed to perform zap and returns them as a transaction group ready to be signed and committed.

        Args:
            address: The account that will be performing the zap.

        Returns:
            A transaction group that when executed will perform the zap.
        """
        return self.pool.prepare_zap_tx_group(self, address)

    def _is_asset_primary(self):
        return self.asset.index == self.pool.primary_asset.index

    def get_zap_params(self) -> ZapParams:
        A, B = self.pool.calculator.get_liquidities(self.asset)
        if A == 0 or B == 0:
            raise ValueError("Cannot create a Zap on empty pool.")

        params = get_constant_product_zap_params(
            A, B, self.amount, self.pool.params.fee_bps, self.pool.params.pact_fee_bps
        )
        if not self._is_asset_primary():
            temp = params.primary_add_liq
            params.primary_add_liq = params.secondary_add_liq - 1
            params.secondary_add_liq = temp
        else:
            params.secondary_add_liq -= 1

        return params

    def prepare_add_liq(self):
        updated_state = self.pool.state
        if self._is_asset_primary():
            updated_state.total_primary += self.params.swap_deposited
            updated_state.total_secondary -= self.params.secondary_add_liq
        else:
            updated_state.total_primary -= self.params.primary_add_liq
            updated_state.total_secondary += self.params.swap_deposited

        pool = copy.copy(self.pool)
        pool.state = updated_state
        return LiquidityAddition(
            pool=pool,
            primary_asset_amount=self.params.primary_add_liq,
            secondary_asset_amount=self.params.secondary_add_liq,
            slippage_pct=self.slippage_pct,
        )
