from datetime import datetime
from typing import cast

import pactsdk
from pactsdk.stableswap_calculator import StableswapCalculator, StableswapParams

from .utils import (
    add_liquidity,
    algod,
    assert_swap,
    create_asset,
    deploy_stableswap_contract,
    make_fresh_testbed,
    new_account,
)


def test_stableswap_asa_to_asa():
    account = new_account()
    pact = pactsdk.PactClient(algod)

    coin_a_index = create_asset(account, "COIN_A", 2)
    coin_b_index = create_asset(account, "COIN_B", 2)

    app_id = deploy_stableswap_contract(account, coin_a_index, coin_b_index)
    pool = pact.fetch_pool_by_id(app_id=app_id)
    assert pool.pool_type == "STABLESWAP"

    add_liquidity(account, pool, 1_000_000, 1_000_000)
    pool.update_state()

    assert pool.state == pactsdk.PoolState(
        total_liquidity=1_000_000,
        total_primary=1_000_000,
        total_secondary=1_000_000,
        primary_asset_price=1,
        secondary_asset_price=1,
    )

    swap = pool.prepare_swap(
        amount=100_000,
        asset=pool.primary_asset,
        slippage_pct=10,
    )
    assert_swap(swap, account)


def test_stableswap_with_changing_amplifier(time):
    testbed = make_fresh_testbed("STABLESWAP", amplifier=100)

    params = cast(StableswapParams, testbed.pool.params)
    swap_calculator = cast(
        StableswapCalculator, testbed.pool.calculator.swap_calculator
    )

    initial_time = params.initial_a_time

    time.move_to(datetime.fromtimestamp(initial_time))

    assert swap_calculator.get_amplifier() == 100

    # Let's increase the amplifier.
    params.future_a = 200
    params.future_a_time += 1000

    swap_args = [2000, 1500, 1000]

    assert swap_calculator.get_amplifier() == 100
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 984
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1017

    time.tick(100)
    assert swap_calculator.get_amplifier() == 110
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 985
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1016

    time.tick(400)
    assert swap_calculator.get_amplifier() == 150
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 989
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1011

    time.tick(600)
    assert swap_calculator.get_amplifier() == 200
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 992
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1008

    time.tick(1400)
    assert swap_calculator.get_amplifier() == 200

    # Let's decrease the amplifier.
    params.initial_a = params.future_a
    params.initial_a_time = int(datetime.now().timestamp())
    params.future_a = 150
    params.future_a_time = params.initial_a_time + 2000
    initial_time = params.initial_a_time

    assert swap_calculator.get_amplifier() == 200
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 992
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1008

    time.tick(100)
    assert swap_calculator.get_amplifier() == 198
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 992
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1008

    time.tick(900)
    assert swap_calculator.get_amplifier() == 175
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 991
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1010

    time.tick(1000)
    assert swap_calculator.get_amplifier() == 150
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 989
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 1011

    time.tick(1000)
    assert swap_calculator.get_amplifier() == 150

    params.future_a = 5000
    assert swap_calculator.get_amplifier() == 5000
    assert swap_calculator.get_swap_gross_amount_received(*swap_args) == 1001
    assert swap_calculator.get_swap_amount_deposited(*swap_args) == 999


def test_stableswap_with_big_amplifier():
    testbed = make_fresh_testbed("STABLESWAP", amplifier=5000)

    add_liquidity(testbed.account, testbed.pool, 20000, 15000)

    swap = testbed.pool.prepare_swap(
        amount=1000,
        asset=testbed.algo,
        slippage_pct=0,
    )

    assert (swap.effect.amount_received + swap.effect.fee) == 1001

    assert_swap(swap, testbed.account)
