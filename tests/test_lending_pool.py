from pactsdk import LendingSwap

from .lending_pool_utils import (
    LendingPoolAdapterTestBed,
    make_fresh_lending_pool_testbed,
)
from .utils import sign_and_send


def assert_swap(testbed: LendingPoolAdapterTestBed, swap: LendingSwap):
    old_state = testbed.lending_pool_adapter.pact_pool.state
    old_primary_holding = testbed.algo.get_holding(testbed.account.address)
    old_secondary_holding = testbed.original_asset.get_holding(testbed.account.address)

    tx_group = testbed.lending_pool_adapter.prepare_swap_tx_group(
        swap, testbed.account.address
    )
    sign_and_send(tx_group, testbed.account)

    testbed.lending_pool_adapter.pact_pool.update_state()

    new_state = testbed.lending_pool_adapter.pact_pool.state
    new_primary_holding = testbed.algo.get_holding(testbed.account.address)
    new_secondary_holding = testbed.original_asset.get_holding(testbed.account.address)

    assert (
        old_primary_holding
        and new_primary_holding
        and old_secondary_holding
        and new_secondary_holding
    )

    if swap.asset_deposited == testbed.algo:
        assert (
            abs(new_state.total_primary - old_state.total_primary)
        ) == swap.f_swap.effect.amount_deposited
        assert (
            abs(old_state.total_secondary - new_state.total_secondary)
            == swap.f_swap.effect.minimum_amount_received
        )

        assert (
            abs(old_primary_holding - new_primary_holding)
            == swap.amount_deposited + swap.tx_fee
        )
        assert (
            abs(new_secondary_holding - old_secondary_holding)
            == swap.minimum_amount_received
        )
    else:
        assert (
            abs(old_state.total_secondary - new_state.total_secondary)
        ) == swap.f_swap.effect.amount_deposited
        assert (
            abs(new_state.total_primary - old_state.total_primary)
            == swap.f_swap.effect.minimum_amount_received
        )

        assert (
            abs(new_secondary_holding - old_secondary_holding) == swap.amount_deposited
        )
        assert abs(old_primary_holding - new_primary_holding) == abs(
            swap.minimum_amount_received - swap.tx_fee
        )


def test_lending_pool_add_and_remove_liquidity():
    testbed = make_fresh_lending_pool_testbed()

    # Add liquidity
    lending_liquidity_addition = testbed.lending_pool_adapter.prepare_add_liquidity(
        100_000, 50_000
    )
    tx_group = testbed.lending_pool_adapter.prepare_add_liquidity_tx_group(
        testbed.account.address, lending_liquidity_addition
    )
    sign_and_send(tx_group, testbed.account)
    testbed.lending_pool_adapter.pact_pool.update_state()

    # Check tokens deposited in Folks contracts.
    assert (
        testbed.lending_pool_adapter.primary_lending_pool.original_asset.get_holding(
            testbed.lending_pool_adapter.primary_lending_pool.escrow_address
        )
        == 100_000 + 300_000  # (+ min balance ALGO)
    )
    assert (
        testbed.lending_pool_adapter.secondary_lending_pool.original_asset.get_holding(
            testbed.lending_pool_adapter.secondary_lending_pool.escrow_address
        )
        == 50_000
    )

    pool_liqudity_addition = lending_liquidity_addition.liquidity_addition
    assert pool_liqudity_addition.primary_asset_amount == 96674
    assert pool_liqudity_addition.secondary_asset_amount == 49860

    # Check Pact pool state.
    assert (
        testbed.lending_pool_adapter.pact_pool.state.total_primary
        == pool_liqudity_addition.primary_asset_amount
    )
    assert (
        testbed.lending_pool_adapter.pact_pool.state.total_secondary
        == pool_liqudity_addition.secondary_asset_amount
    )

    # Check LP the user received.
    assert (
        testbed.lending_pool_adapter.pact_pool.liquidity_asset.get_holding(
            testbed.account.address
        )
        == pool_liqudity_addition.effect.minted_liquidity_tokens
        - 1000  # - blocked LP for first liquidity
    )

    # Remove
    tx_group = testbed.lending_pool_adapter.prepare_remove_liquidity_tx_group(
        testbed.account.address, 20_000
    )
    sign_and_send(tx_group, testbed.account)
    testbed.lending_pool_adapter.pact_pool.update_state()
    assert (
        testbed.lending_pool_adapter.pact_pool.state.total_liquidity
        == pool_liqudity_addition.effect.minted_liquidity_tokens - 20_000
    )

    # Second add liquidity.
    old_lp = testbed.lending_pool_adapter.pact_pool.liquidity_asset.get_holding(
        testbed.account.address
    )
    lending_liquidity_addition = testbed.lending_pool_adapter.prepare_add_liquidity(
        100_000, 50_000
    )
    tx_group = testbed.lending_pool_adapter.prepare_add_liquidity_tx_group(
        testbed.account.address, lending_liquidity_addition
    )
    sign_and_send(tx_group, testbed.account)
    new_lp = testbed.lending_pool_adapter.pact_pool.liquidity_asset.get_holding(
        testbed.account.address
    )
    assert old_lp and new_lp
    minted_tokens = (
        lending_liquidity_addition.liquidity_addition.effect.minted_liquidity_tokens
    )
    assert new_lp - old_lp == minted_tokens


def test_lending_pool_swap_primary_exact():
    testbed = make_fresh_lending_pool_testbed()
    testbed.add_liquidity(100_000, 50_000)

    swap = testbed.lending_pool_adapter.prepare_swap(
        testbed.lending_pool_adapter.primary_lending_pool.original_asset,
        amount=10_000,
        slippage_pct=0,
    )

    assert swap.amount_deposited == 10_000
    assert swap.f_swap.effect.amount_deposited == 9667
    assert swap.amount_received == 4530
    assert swap.f_swap.effect.amount_received == 4518

    assert_swap(testbed, swap)


def test_lending_pool_swap_secondary_exact():
    testbed = make_fresh_lending_pool_testbed()
    testbed.add_liquidity(100_000, 50_000)

    swap = testbed.lending_pool_adapter.prepare_swap(
        testbed.lending_pool_adapter.secondary_lending_pool.original_asset,
        amount=10_000,
        slippage_pct=0,
    )

    assert swap.amount_deposited == 10_000
    assert swap.f_swap.effect.amount_deposited == 9972
    assert swap.amount_received == 16615
    assert swap.f_swap.effect.amount_received == 16063

    assert_swap(testbed, swap)


def test_lending_pool_swap_primary_for_exact():
    testbed = make_fresh_lending_pool_testbed()
    testbed.add_liquidity(100_000, 50_000)

    swap = testbed.lending_pool_adapter.prepare_swap(
        testbed.lending_pool_adapter.primary_lending_pool.original_asset,
        amount=10_000,
        slippage_pct=0,
        swap_for_exact=True,
    )

    assert swap.amount_deposited == 25098
    assert swap.f_swap.effect.amount_deposited == 24263
    assert swap.amount_received == 10_000
    assert swap.f_swap.effect.amount_received == 9972

    assert_swap(testbed, swap)


def test_lending_pool_swap_secondary_for_exact():
    testbed = make_fresh_lending_pool_testbed()
    testbed.add_liquidity(100_000, 50_000)

    swap = testbed.lending_pool_adapter.prepare_swap(
        testbed.lending_pool_adapter.secondary_lending_pool.original_asset,
        amount=10_000,
        slippage_pct=0,
        swap_for_exact=True,
    )

    assert swap.amount_deposited == 5575
    assert swap.f_swap.effect.amount_deposited == 5559
    assert swap.amount_received == 10_000
    assert swap.f_swap.effect.amount_received == 9667

    assert_swap(testbed, swap)
