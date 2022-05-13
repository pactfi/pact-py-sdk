import math
from decimal import Decimal as D

import algosdk
import pytest
from algosdk.error import AlgodHTTPError

import pactsdk

from .matchers import Any
from .utils import (
    Account,
    TestBed,
    add_liqudity,
    algod,
    create_asset,
    deploy_contract,
    make_fresh_testbed,
    new_account,
    sign_and_send,
)


def _test_swap(
    swap: pactsdk.Swap,
    primary_liq: int,
    secondary_liq: int,
    amount_deposited: int,
    account: Account,
):
    assert_swap_effect(swap, primary_liq, secondary_liq, amount_deposited)

    # Perform the swap.
    old_state = swap.pool.state
    swap_tx = swap.prepare_tx(account.address)
    sign_and_send(swap_tx, account)
    swap.pool.update_state()

    # Compare the simulated effect with what really happened on the blockchain.
    assert_pool_state(swap, old_state, swap.pool.state)


def assert_swap_effect(
    swap: pactsdk.Swap,
    primary_liq: int,
    secondary_liq: int,
    amount_deposited: int,
):
    fee_bps = swap.pool.fee_bps
    if swap.asset_deposited == swap.pool.primary_asset:
        gross_amount_received = int(
            D(amount_deposited * secondary_liq) / D(primary_liq + amount_deposited)
        )
    else:
        gross_amount_received = int(
            D(amount_deposited * primary_liq) / D(secondary_liq + amount_deposited)
        )

    amount_received = gross_amount_received * (10_000 - D(fee_bps)) / 10_000

    assert swap.effect == pactsdk.SwapEffect(
        amount_deposited=amount_deposited,
        amount_received=math.floor(amount_received),
        minimum_amount_received=math.floor(
            amount_received - amount_received * D(swap.slippage_pct / 100)
        ),
        fee=round(gross_amount_received - amount_received),
        price=(gross_amount_received / D(swap.asset_in.ratio))
        / (amount_deposited / D(swap.asset_deposited.ratio)),
        primary_asset_price_after_swap=Any(D),
        primary_asset_price_change_pct=Any(D),
        secondary_asset_price_after_swap=Any(D),
        secondary_asset_price_change_pct=Any(D),
    )

    diff_ratio = D(10 ** (swap.asset_in.decimals - swap.asset_deposited.decimals))
    assert (
        int(
            swap.effect.amount_deposited * swap.effect.price * diff_ratio
            - swap.effect.fee
        )
        == swap.effect.amount_received
    )


def assert_pool_state(
    swap: pactsdk.Swap, old_state: pactsdk.PoolState, new_state: pactsdk.PoolState
):
    assert new_state.primary_asset_price == swap.effect.primary_asset_price_after_swap
    assert (
        new_state.secondary_asset_price == swap.effect.secondary_asset_price_after_swap
    )

    assert swap.effect.primary_asset_price_change_pct == (
        (new_state.primary_asset_price / old_state.primary_asset_price) * 100 - 100
    )
    assert swap.effect.secondary_asset_price_change_pct == (
        (new_state.secondary_asset_price / old_state.secondary_asset_price) * 100 - 100
    )

    if swap.asset_deposited == swap.pool.primary_asset:
        assert (
            new_state.total_primary - old_state.total_primary
            == swap.effect.amount_deposited
        )
        assert (
            old_state.total_secondary - new_state.total_secondary
            == swap.effect.amount_received
        )
    else:
        assert (
            old_state.total_primary - new_state.total_primary
            == swap.effect.amount_received
        )
        assert (
            new_state.total_secondary - old_state.total_secondary
            == swap.effect.amount_deposited
        )


def test_swap_with_empty_liquidity(testbed: TestBed):
    with pytest.raises(ValueError, match="Pool is empty and swaps are impossible."):
        testbed.pool.prepare_swap(
            amount=1000,
            asset=testbed.algo,
            slippage_pct=10,
        )


def test_swap_asset_not_in_the_pool(testbed: TestBed):
    shitcoin_index = create_asset(testbed.account)
    shitcoin = testbed.pact.fetch_asset(shitcoin_index)
    with pytest.raises(AssertionError, match=f"Asset {shitcoin.index} not in the pool"):
        testbed.pool.prepare_swap(
            amount=1000,
            asset=shitcoin,
            slippage_pct=10,
        )


def test_swap_primary_with_equal_liquidity(testbed: TestBed):
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
    )

    assert swap.asset_in == testbed.coin
    assert swap.asset_deposited == testbed.algo
    assert swap.slippage_pct == 10

    _test_swap(swap, primary_liq, secondary_liq, amount, testbed.account)


def test_swap_primary_too_high_minimum_amount(testbed: TestBed):
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=0,
    )
    swap.effect.minimum_amount_received = 10 * swap.effect.minimum_amount_received

    assert swap.asset_in == testbed.coin
    assert swap.asset_deposited == testbed.algo
    assert swap.slippage_pct == 0

    # Perform the swap.
    swap_tx = swap.prepare_tx(testbed.account.address)
    with pytest.raises(
        AlgodHTTPError, match="logic eval error: - would result negative."
    ):
        sign_and_send(swap_tx, testbed.account)


def test_swap_secondary_too_high_minimum_amount(testbed: TestBed):
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=0,
    )
    swap.effect.minimum_amount_received = 10 * swap.effect.minimum_amount_received

    assert swap.asset_in == testbed.algo
    assert swap.asset_deposited == testbed.coin
    assert swap.slippage_pct == 0

    # Perform the swap.
    swap_tx = swap.prepare_tx(testbed.account.address)
    with pytest.raises(
        AlgodHTTPError, match="logic eval error: - would result negative."
    ):
        sign_and_send(swap_tx, testbed.account)


def test_swap_primary_with_not_equal_liquidity(testbed: TestBed):
    primary_liq, secondary_liq, amount = 20_000, 25_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.algo,
        slippage_pct=10,
    )

    _test_swap(swap, primary_liq, secondary_liq, amount, testbed.account)


def test_swap_secondary_with_equal_liquidity(testbed: TestBed):
    primary_liq, secondary_liq, amount = 20_000, 20_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=10,
    )

    _test_swap(swap, primary_liq, secondary_liq, amount, testbed.account)


def test_swap_secondary_with_not_equal_liquidity(testbed: TestBed):
    primary_liq, secondary_liq, amount = 25_000, 20_000, 1_000
    add_liqudity(testbed.account, testbed.pool, primary_liq, secondary_liq)

    swap = testbed.pool.prepare_swap(
        amount=amount,
        asset=testbed.coin,
        slippage_pct=10,
    )

    _test_swap(swap, primary_liq, secondary_liq, amount, testbed.account)


def test_swap_with_custom_fee_bps():
    testbed_a = make_fresh_testbed(fee_bps=10)
    testbed_b = make_fresh_testbed(fee_bps=2000)

    assert testbed_a.pool.fee_bps == 10
    assert testbed_b.pool.fee_bps == 2000

    add_liqudity(testbed_a.account, testbed_a.pool, 20_000, 20_000)
    add_liqudity(testbed_b.account, testbed_b.pool, 20_000, 20_000)

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

    swap_a_tx = swap_a.prepare_tx(testbed_a.account.address)
    sign_and_send(swap_a_tx, testbed_a.account)
    testbed_a.pool.update_state()

    swap_b_tx = swap_b.prepare_tx(testbed_b.account.address)
    sign_and_send(swap_b_tx, testbed_b.account)
    testbed_b.pool.update_state()

    assert (
        testbed_a.pool.state.total_secondary == 20_000 - swap_a.effect.amount_received
    )
    assert (
        testbed_b.pool.state.total_secondary == 20_000 - swap_b.effect.amount_received
    )


def test_swap_with_different_slippage(testbed: TestBed):
    add_liqudity(testbed.account, testbed.pool, 20_000, 20_000)

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
        slippage_pct=20,
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
    swap_tx = swap.prepare_tx(testbed.account.address)
    sign_and_send(swap_tx, testbed.account)

    # Swap A and B should fail because slippage is too low.

    swap_a_tx = swap_a.prepare_tx(testbed.account.address)
    with pytest.raises(algosdk.error.AlgodHTTPError):
        sign_and_send(swap_a_tx, testbed.account)

    swap_b_tx = swap_b.prepare_tx(testbed.account.address)
    with pytest.raises(algosdk.error.AlgodHTTPError):
        sign_and_send(swap_b_tx, testbed.account)

    testbed.pool.update_state()
    assert (
        testbed.pool.state.total_secondary == 20_000 - swap.effect.amount_received
    )  # no change yet

    # Swap C and D should pass;
    swap_c_tx = swap_c.prepare_tx(testbed.account.address)
    sign_and_send(swap_c_tx, testbed.account)
    testbed.pool.update_state()
    swapped_c_amount = (
        20_000 - swap.effect.amount_received - testbed.pool.state.total_secondary
    )
    assert swapped_c_amount < swap_c.effect.amount_received
    assert swapped_c_amount > swap_c.effect.minimum_amount_received

    swap_d_tx = swap_d.prepare_tx(testbed.account.address)
    sign_and_send(swap_d_tx, testbed.account)
    testbed.pool.update_state()
    swapped_d_amount = (
        20_000
        - swap.effect.amount_received
        - swapped_c_amount
        - testbed.pool.state.total_secondary
    )
    assert swapped_d_amount < swap_d.effect.amount_received
    assert swapped_d_amount > swap_d.effect.minimum_amount_received


def test_swap_asa_to_asa():
    account = new_account()
    pact = pactsdk.PactClient(algod)

    coin_a_index = create_asset(account, "COIN_A", 3)
    coin_b_index = create_asset(account, "COIN_B", 2)

    app_id = deploy_contract(account, "CONSTANT_PRODUCT", coin_a_index, coin_b_index)
    pool = pact.fetch_pool_by_id(app_id=app_id)

    add_liqudity(account, pool, 20_000, 20_000)
    pool.update_state()

    assert pool.state == pactsdk.PoolState(
        total_liquidity=20_000,
        total_primary=20_000,
        total_secondary=20_000,
        primary_asset_price=D(
            "10"
        ),  # because different decimal places for both assets.
        secondary_asset_price=D("0.1"),
    )

    swap = pool.prepare_swap(
        amount=1000,
        asset=pool.primary_asset,
        slippage_pct=10,
    )
    _test_swap(swap, 20_000, 20_000, 1000, account)
