import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool import Pool


@dataclass
class ConstantProductParams:
    fee_bps: int


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
        return (liq_b * amount_deposited) // (liq_a + amount_deposited)

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        gross_amount_received: int,
    ) -> int:
        deposited = liq_a * gross_amount_received / (liq_b - (gross_amount_received))
        return math.ceil(deposited)
