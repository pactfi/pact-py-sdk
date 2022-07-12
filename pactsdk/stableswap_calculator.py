import logging
import math
import time
from dataclasses import dataclass
from math import isqrt
from typing import TYPE_CHECKING, cast

from .constant_product_calculator import get_constant_product_minted_liquidity_tokens
from .exceptions import PactSdkError

if TYPE_CHECKING:
    from .pool import Pool

logger = logging.getLogger(__name__)

MAX_GET_PRICE_RETRIES = 5


class ConvergenceError(PactSdkError):
    pass


@dataclass
class StableswapParams:
    fee_bps: int
    pact_fee_bps: int
    initial_a: int
    initial_a_time: int
    future_a: int
    future_a_time: int
    precision: int


def get_tx_fee(invariant_iterations: int, extra_margin: int) -> int:
    """To calculate the pool invariant, a Newton-Raphson method is used in both - the SDK and the smart contract.

    Algorand has a limit of the number of operations available in a single app call. To increase the limit, an additional empty inner transaction have to be created. Each extra tx increases tx fee. This functions calculates the fee needed for a swap transaction.

    Args:
        invariant_iterations: Number of iterations of Newton-Raphson interpolation.
        extra_margin: Number of extra inner transactions needed in case of slippage.

    Returns:
        The required fee.

    """
    inner_tx_count = math.ceil((invariant_iterations * 369) / 700)
    # +1 - first obligatory inner tx
    # +1 - app call
    # +2 in total
    return (inner_tx_count + 2 + extra_margin) * 1000


def get_stableswap_minted_liquidity_tokens(
    added_primary: int,
    added_secondary: int,
    total_primary: int,
    total_secondary: int,
    total_liquidity: int,
    amplifier: int,
    precision: int,
    fee_bps: int,
) -> tuple[int, int]:
    """Returns a tuple of minted tokens and total Newton-Raphson iterations (needed for tx fee calculations)."""
    if total_primary + total_secondary == 0:
        minted_tokens = get_constant_product_minted_liquidity_tokens(
            added_primary,
            added_secondary,
            total_primary,
            total_secondary,
            total_liquidity,
        )
        return minted_tokens, 0

    initial_totals = (total_primary, total_secondary)
    updated_totals = (
        total_primary + added_primary,
        total_secondary + added_secondary,
    )

    fees, initial_d, swap_invariant_iterations = get_add_liquidity_fees(
        initial_totals,
        updated_totals,
        fee_bps,
        amplifier,
        precision,
    )
    next_d, next_iterations = get_invariant(
        updated_totals[0] - fees[0],
        updated_totals[1] - fees[1],
        amplifier,
        precision,
    )

    minted_tokens = (total_liquidity * (next_d - initial_d)) // initial_d
    return minted_tokens, swap_invariant_iterations + next_iterations


def get_add_liquidity_bonus_pct(
    added_primary: int,
    added_secondary: int,
    total_primary: int,
    total_secondary: int,
    fee_bps: int,
    amplifier: int,
    precision: int,
) -> float:
    if total_primary + total_secondary == 0:
        return 0

    initial_totals = (total_primary, total_secondary)
    updated_totals = (
        total_primary + added_primary,
        total_secondary + added_secondary,
    )

    fees, initial_d, _ = get_add_liquidity_fees(
        initial_totals,
        updated_totals,
        fee_bps,
        amplifier,
        precision,
    )

    final_balances = (
        updated_totals[0] - fees[0],
        updated_totals[1] - fees[1],
    )

    final_d, _ = get_invariant(
        final_balances[0],
        final_balances[1],
        amplifier,
        precision,
    )

    # Calculate the gain in absolute terms, considering that each token is worth 1.
    total_added = added_primary + added_secondary
    return ((final_d - initial_d) / total_added - 1) * 100


def get_add_liquidity_fees(
    initial_totals: tuple[int, int],
    updated_totals: tuple[int, int],
    fee_bps: int,
    amplifier: int,
    precision: int,
) -> tuple[tuple[int, int], int, int]:
    n = 2

    initial_d, initial_iterations = get_invariant(
        initial_totals[0],
        initial_totals[1],
        amplifier,
        precision,
    )

    # Calculate the invariant as if all tokens were added to the pool
    next_d, next_iterations = get_invariant(
        updated_totals[0],
        updated_totals[1],
        amplifier,
        precision,
    )

    perfect_balances = [(next_d * total) // initial_d for total in initial_totals]
    deltas = (
        abs(updated_totals[0] - perfect_balances[0]),
        abs(updated_totals[1] - perfect_balances[1]),
    )

    fees = tuple((delta * fee_bps * n) // (10_000 * (4 * (n - 1))) for delta in deltas)

    return (fees[0], fees[1]), initial_d, initial_iterations + next_iterations


def get_swap_gross_amount_received(
    liq_a: int, liq_b: int, amount_deposited: int, amplifier: int, precision: int
) -> tuple[int, int]:
    invariant, iterations = get_invariant(liq_a, liq_b, amplifier, precision)
    new_liq_b = get_new_liq(liq_a + amount_deposited, amplifier, invariant, precision)
    return liq_b - new_liq_b, iterations


def get_swap_amount_deposited(
    liq_a: int,
    liq_b: int,
    gross_amount_received: int,
    amplifier: int,
    precision: int,
) -> tuple[int, int]:
    invariant, iterations = get_invariant(liq_a, liq_b, amplifier, precision)
    new_liq_a = get_new_liq(
        liq_b - gross_amount_received, amplifier, invariant, precision
    )
    return new_liq_a - liq_a, iterations


def get_invariant(liq_a: int, liq_b: int, amp: int, precision: int) -> tuple[int, int]:
    """Uses a Newton-Raphson method to calculate the pool invariant.

    Returns:
        A tuple of invariant and number of iterations required to calculate the invariant.
    """
    tokens_total = liq_a + liq_b
    S = tokens_total
    if S == 0:
        return S, 0

    D = S
    Ann = amp * 4
    i = 0
    while i < 64:
        i += 1
        D_P = D * D * D
        D_P //= liq_a * liq_b * 4

        Dprev = D
        numerator = D * ((Ann * S) // precision + D_P * 2)
        divisor = ((Ann - precision) * D) // precision + (2 + 1) * D_P
        D = numerator // divisor
        if D > Dprev:
            if D - Dprev <= 1:
                break
        elif Dprev - D <= 1:
            break
    if i == 64:
        raise ConvergenceError(f"Didn't converge {Dprev=}, {D=}")
    return D, i


def get_new_liq(liq_other: int, amplifier: int, inv: int, precision: int) -> int:
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


def get_amplifier(
    timestamp: int,
    initial_a: int,
    initial_a_time: int,
    future_a: int,
    future_a_time: int,
) -> int:
    """Calculates the amplifier at specified timestamp using linear interpolation."""
    dt = future_a_time - initial_a_time
    dv = future_a - initial_a
    if not dt or not dv:
        return future_a

    dv_per_s = dv / dt

    min_a, max_a = (
        (initial_a, future_a) if future_a > initial_a else (future_a, initial_a)
    )

    current_a = initial_a + (timestamp - initial_a_time) * dv_per_s
    return max(min_a, min(max_a, math.ceil(current_a)))


class StableswapCalculator:
    """An implementation of a math behind stableswap pools."""

    swap_invariant_iterations = 0
    """Keeps the amount of iteration used to calculate invariant in the last call to getSwapGrossAmountReceived or getSwapAmountDeposited. Needed to calculate transaction fee."""

    mint_tokens_invariant_iterations = 0
    """The same as swap_invariant_iterations but for adding liquidity."""

    def __init__(self, pool: "Pool"):
        self.pool = pool

    @property
    def stableswap_params(self) -> StableswapParams:
        return cast(StableswapParams, self.pool.params)

    def get_amplifier(self):
        params = self.stableswap_params
        return get_amplifier(
            int(time.time()),
            params.initial_a,
            params.initial_a_time,
            params.future_a,
            params.future_a_time,
        )

    def get_price(self, liq_a: float, liq_b: float) -> float:
        """May return zero for highly unbalanced pools."""
        if not liq_a or not liq_b:
            return 0

        ratio = self.pool.primary_asset.ratio
        if ratio != self.pool.secondary_asset.ratio:
            logger.warning(
                "Number of decimals differs between primary and secondary asset. Stableswap does not support this scenario correctly.",
            )

        return self._get_price(liq_a, liq_b, MAX_GET_PRICE_RETRIES)

    def _get_price(self, liq_a: float, liq_b: float, retries: int) -> float:
        """
        Price is calculated by simulating a swap for 10**6 of micro values.
        This price is highly inaccurate for low liquidity pools.
        In case of ConvergenceError we try to simulate a swap using a different swap amount.
        Returns zero if all retries will fail.
        """
        if retries <= 0:
            return 0.0

        ratio = self.pool.primary_asset.ratio

        liq_a *= ratio
        liq_b *= ratio

        # The division helps minimize price impact of simulated swap.
        amount_deposited = 10 ** (6 + MAX_GET_PRICE_RETRIES - retries)
        amount_deposited = min(amount_deposited, int(liq_a // 100), int(liq_b // 100))

        try:
            amount_received = self.get_swap_gross_amount_received(
                int(liq_b), int(liq_a), int(amount_deposited), save_iterations=False
            )
            if amount_received == 0:
                return self._get_price(liq_a, liq_b, retries - 1)

            return amount_deposited / amount_received
        except ConvergenceError:
            return self._get_price(liq_a, liq_b, retries - 1)

    def get_swap_gross_amount_received(
        self,
        liq_a: int,
        liq_b: int,
        amount_deposited: int,
        save_iterations=True,
    ) -> int:
        amplifier = self.get_amplifier()
        precision = self.stableswap_params.precision
        amount_received, iterations = get_swap_gross_amount_received(
            liq_a, liq_b, amount_deposited, amplifier, precision
        )
        if save_iterations:
            self.swap_invariant_iterations = iterations
        return amount_received

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        gross_amount_received: int,
        save_iterations=True,
    ) -> int:
        amplifier = self.get_amplifier()
        precision = self.stableswap_params.precision
        amount_deposited, iterations = get_swap_amount_deposited(
            liq_a, liq_b, gross_amount_received, amplifier, precision
        )
        if save_iterations:
            self.swap_invariant_iterations = iterations
        return amount_deposited

    def get_minted_liquidity_tokens(self, added_liq_a: int, added_liq_b: int) -> int:
        precision = self.stableswap_params.precision
        amplifier = self.get_amplifier()

        minted_tokens, iterations = get_stableswap_minted_liquidity_tokens(
            added_liq_a,
            added_liq_b,
            self.pool.state.total_primary,
            self.pool.state.total_secondary,
            self.pool.state.total_liquidity,
            amplifier,
            precision,
            self.pool.fee_bps,
        )

        self.mint_tokens_invariant_iterations = iterations

        if minted_tokens > 0:
            return minted_tokens

        if minted_tokens == 0:
            raise PactSdkError(
                "Amount of minted liquidity tokens must be greater then 0.",
            )

        """
        Add liquidity fee is always taken from both assets, even if the user provided only one asset as the liquidity. In self case, the fee is taken from current pool's liquidity.
        If the current liquidity is not high enough to cover the fee, the contract will fail.
        In the SDK calculations self results in minted_tokens < 0.
        """
        raise PactSdkError(
            "Pool liquidity too low to cover add liquidity fee.",
        )
