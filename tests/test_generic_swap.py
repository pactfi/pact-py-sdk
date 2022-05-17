import algosdk
import pytest
from algosdk.error import AlgodHTTPError

import pactsdk
from pactsdk.transaction_group import TransactionGroup

from .utils import (
    POOL_TYPES,
    add_liquidity,
    assert_swap,
    create_asset,
    make_fresh_testbed,
    new_account,
    sign_and_send,
)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_with_empty_liquidity(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    with pytest.raises(ValueError, match="Pool is empty and swaps are impossible."):
        testbed.pool.prepare_swap(
            amount=1000,
            asset=testbed.algo,
            slippage_pct=10,
        )


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_asset_not_in_the_pool(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    shitcoin_index = create_asset(testbed.account)
    shitcoin = testbed.pact.fetch_asset(shitcoin_index)
    with pytest.raises(AssertionError, match=f"Asset {shitcoin.index} not in the pool"):
        testbed.pool.prepare_swap(
            amount=1000,
            asset=shitcoin,
            slippage_pct=10,
        )


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_primary_with_equal_liquidity(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
    )

    assert swap.asset_received == testbed.coin
    assert swap.asset_deposited == testbed.algo
    assert swap.slippage_pct == 10

    assert_swap(swap, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_primary_too_high_minimum_amount(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=0,
    )
    swap.effect.minimum_amount_received = 10 * swap.effect.minimum_amount_received

    assert swap.asset_received == testbed.coin
    assert swap.asset_deposited == testbed.algo
    assert swap.slippage_pct == 0

    # Perform the swap.
    swap_tx_group = swap.prepare_tx_group(testbed.account.address)
    with pytest.raises(
        AlgodHTTPError, match="logic eval error: - would result negative."
    ):
        sign_and_send(swap_tx_group, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_secondary_too_high_minimum_amount(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=0,
    )
    swap.effect.minimum_amount_received = 10 * swap.effect.minimum_amount_received

    assert swap.asset_received == testbed.algo
    assert swap.asset_deposited == testbed.coin
    assert swap.slippage_pct == 0

    # Perform the swap.
    swap_tx_group = swap.prepare_tx_group(testbed.account.address)
    with pytest.raises(
        AlgodHTTPError, match="logic eval error: - would result negative."
    ):
        sign_and_send(swap_tx_group, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_primary_with_not_equal_liquidity(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 25_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
    )

    assert_swap(swap, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_secondary_with_equal_liquidity(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=10,
    )

    assert_swap(swap, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_secondary_with_not_equal_liquidity(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 25_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=10,
    )

    assert_swap(swap, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_with_custom_fee_bps(pool_type: pactsdk.pool.PoolType):
    testbed_a = make_fresh_testbed(pool_type, fee_bps=10)
    testbed_b = make_fresh_testbed(pool_type, fee_bps=2000)

    assert testbed_a.pool.params.fee_bps == 10
    assert testbed_b.pool.params.fee_bps == 2000

    add_liquidity(testbed_a.account, testbed_a.pool, 20_000, 20_000)
    add_liquidity(testbed_b.account, testbed_b.pool, 20_000, 20_000)

    swap_a = testbed_a.pool.prepare_swap(
        amount=10_000,
        asset=testbed_a.algo,
        slippage_pct=10,
    )
    swap_b = testbed_b.pool.prepare_swap(
        amount=10_000,
        asset=testbed_b.algo,
        slippage_pct=10,
    )

    assert swap_b.effect.price == swap_a.effect.price
    assert swap_b.effect.fee > swap_a.effect.fee
    assert swap_b.effect.amount_received < swap_a.effect.amount_received

    # Perform the swaps and check if the simulated effect matches what really happened in the blockchain.

    swap_a_tx = swap_a.prepare_tx_group(testbed_a.account.address)
    sign_and_send(swap_a_tx, testbed_a.account)
    testbed_a.pool.update_state()

    swap_b_tx = swap_b.prepare_tx_group(testbed_b.account.address)
    sign_and_send(swap_b_tx, testbed_b.account)
    testbed_b.pool.update_state()

    assert (
        testbed_a.pool.state.total_secondary == 20_000 - swap_a.effect.amount_received
    )
    assert (
        testbed_b.pool.state.total_secondary == 20_000 - swap_b.effect.amount_received
    )


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_with_different_slippage(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    add_liquidity(testbed.account, testbed.pool, 20_000, 20_000)

    with pytest.raises(ValueError, match="Splippage must be between 0 and 100"):
        testbed.pool.prepare_swap(
            amount=10_000,
            asset=testbed.algo,
            slippage_pct=-1,
        )

    with pytest.raises(ValueError, match="Splippage must be between 0 and 100"):
        testbed.pool.prepare_swap(
            amount=10_000,
            asset=testbed.algo,
            slippage_pct=100.1,
        )

    swap_a = testbed.pool.prepare_swap(
        amount=10_000,
        asset=testbed.algo,
        slippage_pct=0,
    )
    swap_b = testbed.pool.prepare_swap(
        amount=10_000,
        asset=testbed.algo,
        slippage_pct=2,
    )
    swap_c = testbed.pool.prepare_swap(
        amount=10_000,
        asset=testbed.algo,
        slippage_pct=60,
    )
    swap_d = testbed.pool.prepare_swap(
        amount=10_000,
        asset=testbed.algo,
        slippage_pct=100,
    )

    assert swap_a.effect.minimum_amount_received == swap_a.effect.amount_received

    assert swap_b.effect.minimum_amount_received < swap_b.effect.amount_received
    assert swap_b.effect.minimum_amount_received > 0

    assert swap_c.effect.minimum_amount_received < swap_c.effect.amount_received
    assert swap_c.effect.minimum_amount_received < swap_b.effect.minimum_amount_received
    assert swap_c.effect.minimum_amount_received > 0

    assert swap_d.effect.minimum_amount_received == 0

    # Now let's do a swap that change the price.
    swap = testbed.pool.prepare_swap(
        amount=10_000,
        asset=testbed.algo,
        slippage_pct=0,
    )
    swap_tx_group = swap.prepare_tx_group(testbed.account.address)
    sign_and_send(swap_tx_group, testbed.account)

    # Swap A and B should fail because slippage is too low.

    swap_a_tx_group = swap_a.prepare_tx_group(testbed.account.address)
    with pytest.raises(algosdk.error.AlgodHTTPError):
        sign_and_send(swap_a_tx_group, testbed.account)

    swap_b_tx_group = swap_b.prepare_tx_group(testbed.account.address)
    with pytest.raises(algosdk.error.AlgodHTTPError):
        sign_and_send(swap_b_tx_group, testbed.account)

    testbed.pool.update_state()
    assert (
        testbed.pool.state.total_secondary == 20_000 - swap.effect.amount_received
    )  # no change yet

    # Swap C and D should pass;
    swap_c_tx_group = swap_c.prepare_tx_group(testbed.account.address)
    sign_and_send(swap_c_tx_group, testbed.account)
    testbed.pool.update_state()
    swapped_c_amount = (
        20_000 - swap.effect.amount_received - testbed.pool.state.total_secondary
    )
    assert swapped_c_amount < swap_c.effect.amount_received
    assert swapped_c_amount > swap_c.effect.minimum_amount_received

    swap_d_tx_group = swap_d.prepare_tx_group(testbed.account.address)
    sign_and_send(swap_d_tx_group, testbed.account)
    testbed.pool.update_state()
    swapped_d_amount = (
        20_000
        - swap.effect.amount_received
        - swapped_c_amount
        - testbed.pool.state.total_secondary
    )
    assert swapped_d_amount < swap_d.effect.amount_received
    assert swapped_d_amount > swap_d.effect.minimum_amount_received


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_and_optin_in_a_single_group(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    other_account = new_account()
    primaryLiq, secondaryLiq, amount = [20_000, 20_000, 1_000]
    add_liquidity(testbed.account, testbed.pool, primaryLiq, secondaryLiq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
    )

    suggested_params = testbed.pact.algod.suggested_params()
    opt_in_tx = testbed.coin.build_opt_in_tx(other_account.address, suggested_params)
    swap_txs = testbed.pool.build_swap_txs(
        swap=swap,
        address=other_account.address,
        suggested_params=suggested_params,
    )
    txs = [opt_in_tx, *swap_txs]

    group = TransactionGroup(txs)
    sign_and_send(group, other_account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_primary_with_equal_liquidity_reversed(pool_type: pactsdk.pool.PoolType):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    reversed_swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
        reverse=True,
    )

    assert reversed_swap.asset_received == testbed.coin
    assert reversed_swap.asset_deposited == testbed.algo
    assert reversed_swap.slippage_pct == 10
    assert reversed_swap.effect.amount_received == 1000
    assert reversed_swap.effect.amount_deposited > 1000

    swap = testbed.pool.prepare_swap(
        amount=reversed_swap.effect.amount_deposited,
        asset=testbed.algo,
        slippage_pct=10,
    )

    assert swap.effect.fee == reversed_swap.effect.fee
    assert swap.effect.amount_deposited == reversed_swap.effect.amount_deposited
    assert swap.effect.amount_received == reversed_swap.effect.amount_received

    assert_swap(reversed_swap, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_swap_primary_with_not_equal_liquidity_reversed(
    pool_type: pactsdk.pool.PoolType,
):
    testbed = make_fresh_testbed(pool_type)
    primary_liq, secondary_liq, amount = 15_000, 25_000, 2_000
    add_liquidity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    reversed_swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
        reverse=True,
    )

    assert reversed_swap.effect.amount_received == 2000

    swap = testbed.pool.prepare_swap(
        amount=reversed_swap.effect.amount_deposited,
        asset=testbed.algo,
        slippage_pct=10,
    )

    assert swap.effect.fee == reversed_swap.effect.fee
    assert swap.effect.amount_deposited == reversed_swap.effect.amount_deposited
    assert swap.effect.amount_received == reversed_swap.effect.amount_received

    assert_swap(reversed_swap, testbed.account)
