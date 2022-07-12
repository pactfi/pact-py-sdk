import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pactsdk.exceptions import PactSdkError

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class ConstantProductParams:
    fee_bps: int
    pact_fee_bps: int


def get_swap_gross_amount_received(
    liq_a: int, liq_b: int, amount_deposited: int
) -> int:
    return (liq_b * amount_deposited) // (liq_a + amount_deposited)


def get_swap_amount_deposited(
    liq_a: int,
    liq_b: int,
    gross_amount_received: int,
) -> int:
    deposited = liq_a * gross_amount_received / (liq_b - (gross_amount_received))
    return math.ceil(deposited)


def get_constant_product_minted_liquidity_tokens(
    added_primary: int,
    added_secondary: int,
    total_primary: int,
    total_secondary: int,
    total_liquidity: int,
) -> int:
    if total_primary + total_secondary == 0:
        return math.isqrt(added_primary * added_secondary)

    lt_a = (added_primary * total_liquidity) // total_primary
    lt_b = (added_secondary * total_liquidity) // total_secondary
    return lt_b if lt_a > lt_b else lt_a


class ConstantProductCalculator:
    """An implementation of a math behind constant product pools."""

    def __init__(self, pool: "Pool"):
        self.pool = pool

    def get_price(self, liq_a: float, liq_b: float) -> float:
        if not liq_a or not liq_b:
            return 0
        return liq_b / liq_a

    def get_swap_gross_amount_received(
        self, liq_a: int, liq_b: int, amount_deposited: int
    ) -> int:
        return get_swap_gross_amount_received(liq_a, liq_b, amount_deposited)

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        gross_amount_received: int,
    ) -> int:
        return get_swap_amount_deposited(liq_a, liq_b, gross_amount_received)

    def get_minted_liquidity_tokens(self, added_liq_a: int, added_liq_b: int) -> int:
        minted_tokens = get_constant_product_minted_liquidity_tokens(
            added_liq_a,
            added_liq_b,
            self.pool.state.total_primary,
            self.pool.state.total_secondary,
            self.pool.state.total_liquidity,
        )

        if minted_tokens > 0:
            return minted_tokens

        raise PactSdkError(
            "Amount of minted liquidity tokens must be greater then 0.",
        )
