import math
from typing import TYPE_CHECKING, Protocol

from pactsdk.constant_product_calculator import ConstantProductCalculator
from pactsdk.exceptions import PactSdkError
from pactsdk.stableswap_calculator import StableswapCalculator

from .asset import Asset

if TYPE_CHECKING:
    from .pool import Pool


class SwapCalculator(Protocol):
    pool: "Pool"

    def get_price(self, liq_a: float, liq_b: float) -> float:
        """Calculates the price of assets. Accepts and returns decimal values.

        Args:
            liq_a: Primary liquidity if calculating price for primary asset, secondary otherwise.
            liq_b: Secondary liquidity if calculating price for primary asset, primary otherwise.

        Returns:
            The price of one asset in relation to the other.
        """
        ...

    def get_swap_gross_amount_received(
        self,
        liq_a: int,
        liq_b: int,
        amount_deposited: int,
    ) -> int:
        """Converts amountDeposited to amountReceived. Ignores fee calculations.

        Args:
            liq_a: Primary liquidity if swapping primary asset, secondary otherwise.
            liq_b: Secondary liquidity if swapping primary asset, primary otherwise.
            amount_deposited: Amount of the asset deposited in the contract.

        Returns:
            Amount of asset received from the contract after swap.
        """
        ...

    def get_swap_amount_deposited(
        self,
        liq_a: int,
        liq_b: int,
        amount_received: int,
    ) -> int:
        """Converts amountReceived to amountDeposited. Ignores fee calculations.

        Args:
            liq_a: Primary liquidity if swapping primary asset, secondary otherwise.
            liq_b: Secondary liquidity if swapping primary asset, primary otherwise.
            amount_received: Amount of asset the user want to receive from the swap.

        Returns:
            Amount of the asset the user has to deposit in the contract.
        """
        ...

    def get_minted_liquidity_tokens(self, added_liq_a: int, added_liq_b: int) -> int:
        """Returns amount of liquidity tokens that are going to be minted when adding liquidity.

        Args:
            added_liq_a: Amount of primary asset to add to the pool.
            added_liq_b: Amount of secondary asset to add to the pool.

        Returns:
            Amount of liquidity tokens that will be minted and given to user.
        """
        ...


class PoolCalculator:
    """Contains functions for calculation statistics and other numerical data about the pool.

    The pool calculator uses internal data from the pool to calculate values like the Prices, Net Amounts and values for the swap. Uses different formulas based on pool type.
    """

    def __init__(self, pool: "Pool"):
        self.pool = pool

        self.swap_calculator: SwapCalculator
        if pool.pool_type in ["CONSTANT_PRODUCT", "NFT_CONSTANT_PRODUCT"]:
            self.swap_calculator = ConstantProductCalculator(pool)
        elif pool.pool_type == "STABLESWAP":
            self.swap_calculator = StableswapCalculator(pool)
        else:
            raise PactSdkError(f"Unknown pool type: ${pool.pool_type}")

    @property
    def primary_asset_amount(self) -> int:
        return self.pool.internal_state.A

    @property
    def secondary_asset_amount(self) -> int:
        return self.pool.internal_state.B

    @property
    def primary_asset_amount_decimal(self) -> float:
        return self.pool.internal_state.A / self.pool.primary_asset.ratio

    @property
    def secondary_asset_amount_decimal(self) -> float:
        return self.pool.internal_state.B / self.pool.secondary_asset.ratio

    @property
    def is_empty(self) -> bool:
        """Checks if the pool is currently empty.

        A pool is empty if either the primary or secondary asset is zero.

        Returns:
            True if the pool is empty, False otherwise.
        """
        return self.primary_asset_amount == 0 or self.secondary_asset_amount == 0

    @property
    def primary_asset_price(self) -> float:
        """
        Returns:
            Amount of secondary assets for a single primary asset.
        """
        return self.swap_calculator.get_price(
            self.primary_asset_amount_decimal, self.secondary_asset_amount_decimal
        )

    @property
    def secondary_asset_price(self) -> float:
        """
        Returns:
            Amount of primary assets for a single secondary asset.
        """
        return self.swap_calculator.get_price(
            self.secondary_asset_amount_decimal,
            self.primary_asset_amount_decimal,
        )

    def amount_deposited_to_net_amount_received(
        self, asset: Asset, amount_deposited: int
    ) -> int:
        """Converts amount deposited in the contract to amount received from the contract. Includes fee calculations.

        Args:
            asset: Asset to deposit in the contract.
            amount_deposited: Amount to deposit in the contract.

        Returns:
            The amount to receive from the contract.
        """
        gross_amount_received = self._amount_deposited_to_gross_amount_received(
            asset, amount_deposited
        )
        fee = self.get_fee_from_gross_amount(gross_amount_received)
        return gross_amount_received - fee

    def net_amount_received_to_amount_deposited(
        self, asset: Asset, net_amount_received: int
    ) -> int:
        """Converts amount received from the contract to amount deposited in the contract.

        Args:
            asset: Asset to deposit in the contract.
            amount_deposited: Amount to receive from the contract.

        Returns:
            The amount to deposit in the contract.
        """
        fee = self.get_fee_from_net_amount(net_amount_received)
        net_amount_received += fee
        return self._gross_amount_received_to_amount_deposited(
            asset, net_amount_received
        )

    def get_fee_from_gross_amount(self, gross_amount: int) -> int:
        """Calculates the fee from the gross amount based on pool's fee_bps.

        Args:
            gross_amount: The amount to receive from the contract not yet lessened by the fee.

        Returns:
            The calculated fee.
        """
        return gross_amount - (gross_amount * (10_000 - self.pool.fee_bps)) // 10_000

    def get_fee_from_net_amount(self, net_amount: int) -> int:
        """Calculates the fee from the net amount based on pool's fee_bps. This is used in the swap for exact calculations.

        Args:
            net_amount: The amount to receive from the contract already lessened by the fee.

        Returns:
            The calculated fee.
        """
        return math.ceil(
            net_amount / ((10_000 - self.pool.fee_bps) / 10_000) - net_amount
        )

    def _gross_amount_received_to_amount_deposited(
        self,
        asset: Asset,
        int_gross_amount_received: int,
    ) -> int:
        A, B = self.get_liquidities(asset)
        return self.swap_calculator.get_swap_amount_deposited(
            A,
            B,
            int_gross_amount_received,
        )

    def _amount_deposited_to_gross_amount_received(
        self,
        asset: Asset,
        amount_deposited: int,
    ) -> int:
        A, B = self.get_liquidities(asset)
        return self.swap_calculator.get_swap_gross_amount_received(
            A,
            B,
            amount_deposited,
        )

    def get_liquidities(self, asset: Asset) -> tuple[int, int]:
        """Returns the array of liquidities from the pool, sorting them by setting provided asset as primary.

        Args:
            asset: The asset that is supposed to be the primary one.

        Returns:
            Total liquidities of assets.
        """
        A, B = [self.primary_asset_amount, self.secondary_asset_amount]
        if asset != self.pool.primary_asset:
            A, B = B, A
        return A, B

    def get_minimum_amount_received(
        self, asset: Asset, amount: int, slippage_pct: float
    ) -> int:
        """Based on the deposited amount and a slippage, calculate the minimum amount the user will receive from the contract.

        Args:
            asset: The asset to deposit in the contract.
            amount_deposited: The amount to deposit in the contract.
            slippage_pct: Slippage in percents.

        Returns:
            The minimum amount to receive from the contract.
        """

        amount_received = self.amount_deposited_to_net_amount_received(asset, amount)
        return math.floor(amount_received - (amount_received * (slippage_pct / 100)))

    def get_fee(self, asset: Asset, amount_deposited: int) -> int:
        """Calculates the exchange fee based on deposited amount.

        Args:
            asset: The asset to deposit in the contract.
            amount_deposited: The amount to deposit in the contract.

        Returns:
            The calculated fee.
        """
        return self._amount_deposited_to_gross_amount_received(
            asset, amount_deposited
        ) - (self.amount_deposited_to_net_amount_received(asset, amount_deposited))

    def get_asset_price_after_liq_change(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> float:
        """Simulates new asset price after changing the pool's liquidity.

        Args:
            asset: The asset for which to calculate the price for.
            primary_liq_change: The change of primary liquidity on the pool.
            secondary_liq_change: The change of secondary liquidity on the pool.

        Returns:
            New asset price.
        """
        new_primary_liq = (
            self.primary_asset_amount + primary_liq_change
        ) / self.pool.primary_asset.ratio
        new_secondary_liq = (
            self.secondary_asset_amount + secondary_liq_change
        ) / self.pool.secondary_asset.ratio

        if asset == self.pool.primary_asset:
            return self.swap_calculator.get_price(new_primary_liq, new_secondary_liq)
        return self.swap_calculator.get_price(new_secondary_liq, new_primary_liq)

    def get_price_impact_pct(
        self,
        asset: Asset,
        primary_liq_change: int,
        secondary_liq_change: int,
    ) -> float:
        """Calculates the price impact of changing the liquidity in a certain way.

        Args:
            asset: The asset for which to calculate the price impact for.
            primary_liq_change: The change of primary liquidity on the pool.
            secondary_liq_change: The change of secondary liquidity on the pool.

        Returns:
            The asset price impact.
        """
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

    def get_swap_price(self, asset_deposited: Asset, amount_deposited: int) -> float:
        """Calculates the price for which the asset in going to be swapped.

        Args:
            asset_deposited: The asset deposited in the contract.
            amount_deposited: The amount deposited in the contract.

        Returns:
            The price of deposited asset in relation to received asset.
        """
        asset_received = self.pool.get_other_asset(asset_deposited)
        amount_received = self._amount_deposited_to_gross_amount_received(
            asset_deposited, amount_deposited
        )
        diff_ratio = asset_deposited.ratio / asset_received.ratio
        return amount_received / amount_deposited * diff_ratio
