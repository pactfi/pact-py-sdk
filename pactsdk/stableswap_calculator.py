import logging
import math
import time
from dataclasses import dataclass
from math import isqrt
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .pool import Pool

logger = logging.getLogger(__name__)


@dataclass
class StableswapParams:
    fee_bps: int
    pact_fee_bps: int
    initial_a: int
    initial_a_time: int
    future_a: int
    future_a_time: int
    precision: int


class StableswapCalculator:
    """An implementation of a math behind stableswap pools."""

    def __init__(self, pool: "Pool"):
        self.pool = pool

    @property
    def stableswap_params(self) -> StableswapParams:
        return cast(StableswapParams, self.pool.params)

    def get_amplifier(self) -> int:
        # Linear interpolation based on current timestamp.
        params = self.stableswap_params
        now = int(time.time())
        dt = params.future_a_time - params.initial_a_time
        dv = params.future_a - params.initial_a
        if not dt or not dv:
            return params.future_a

        dv_per_ms = dv / dt

        min_a, max_a = (
            (params.initial_a, params.future_a)
            if params.future_a > params.initial_a
            else (params.future_a, params.initial_a)
        )

        current_a = params.initial_a + (now - params.initial_a_time) * dv_per_ms
        return max(min_a, min(max_a, math.ceil(current_a)))

    def get_price(self, liq_a: float, liq_b: float) -> float:
        if not liq_a or not liq_b:
            return 0

        ratio = self.pool.primary_asset.ratio
        if ratio != self.pool.secondary_asset.ratio:
            logger.warning(
                "Number of decimals differs between primary and secondary asset. Stableswap does not support this scenario correctly.",
            )

        # Price is calculated by simulating a swap for 1 token.
        # This price is highly inaccurate for low liquidity pools.
        liq_a *= ratio
        liq_b *= ratio

        # The division helps minimize price impact of simulated swap.
        amount_deposited = min(ratio, liq_a // 100, liq_b // 100)
        amount_received = self.get_swap_gross_amount_received(
            int(liq_b),
            int(liq_a),
            int(amount_deposited),
        )
        return amount_deposited / amount_received

    def get_swap_gross_amount_received(
        self,
        liq_a: int,
        liq_b: int,
        amount_deposited: int,
    ) -> int:
        amplifier = self.get_amplifier()
        invariant = self.get_invariant(liq_a, liq_b, amplifier)
        new_liq_b = self.get_new_liq(
            liq_a + amount_deposited,
            amplifier,
            invariant,
        )
        return liq_b - new_liq_b

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        gross_amount_received: int,
    ) -> int:
        amplifier = self.get_amplifier()
        invariant = self.get_invariant(liq_a, liq_b, amplifier)
        new_liq_a = self.get_new_liq(
            liq_b - gross_amount_received,
            amplifier,
            invariant,
        )
        return new_liq_a - liq_a

    def get_invariant(self, liq_a: int, liq_b: int, amp: int) -> int:

        tokens_total = liq_a + liq_b
        S = tokens_total
        if S == 0:
            return S

        precision = self.stableswap_params.precision

        D = S
        Ann = amp * 4
        i = 0
        while i < 255:
            i += 1
            D_P = D
            for _x in (liq_a, liq_b):
                D_P = D_P * D // (_x * 2)
            Dprev = D
            numerator = D * ((Ann * S) // precision + D_P * 2)
            divisor = ((Ann - precision) * D) // precision + (2 + 1) * D_P
            D = numerator // divisor
            if D > Dprev:
                if D - Dprev <= 1:
                    break
            elif Dprev - D <= 1:
                break
        if i == 255:
            raise Exception(f"Didn't converge {Dprev=}, {D=}")
        return D

    def get_new_liq(self, liq_other: int, amplifier: int, inv: int) -> int:
        precision = self.stableswap_params.precision
        S = liq_other
        D = inv
        A = amplifier
        P = liq_other
        Ann = A * 4

        b = S + (D * precision) // Ann
        c = (precision * (D**3)) // (4 * P * Ann)

        a_q = 1
        b_q = b - D
        c_q = -c

        delta = b_q * b_q - 4 * a_q * c_q
        return (-b_q + isqrt(delta)) // (2 * a_q)
