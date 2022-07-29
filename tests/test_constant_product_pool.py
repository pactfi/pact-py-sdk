from dataclasses import asdict

import pactsdk

from .utils import TestBed, sign_and_send


def test_constant_product_pool_e2e_scenario(testbed: TestBed):
    __base_e2e_scenario(testbed)


def test_constant_product_v_1_pool_e2e_scenario(testbed_v_1: TestBed):
    __base_e2e_scenario(testbed_v_1)


def __base_e2e_scenario(testbed: TestBed):
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=0,
        total_primary=0,
        total_secondary=0,
        primary_asset_price=0,
        secondary_asset_price=0,
    )

    # Opt in for liquidity asset.
    liq_opt_in_tx = testbed.pool.liquidity_asset.prepare_opt_in_tx(
        testbed.account.address
    )
    sign_and_send(liq_opt_in_tx, testbed.account)

    # Add liquidity.
    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=100_000,
        secondary_asset_amount=100_000,
    )
    add_liq_tx_group = liquidity_addition.prepare_tx_group(
        address=testbed.account.address,
    )
    assert add_liq_tx_group.group_id
    assert len(add_liq_tx_group.transactions) == 3
    sign_and_send(add_liq_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=100_000,
        total_primary=100_000,
        total_secondary=100_000,
        primary_asset_price=1,
        secondary_asset_price=1,
    )

    # Remove liquidity.
    remove_liq_tx_group = testbed.pool.prepare_remove_liquidity_tx_group(
        address=testbed.account.address,
        amount=10_000,
    )
    assert len(remove_liq_tx_group.transactions) == 2
    sign_and_send(remove_liq_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=90_000,
        total_primary=90_000,
        total_secondary=90_000,
        primary_asset_price=1,
        secondary_asset_price=1,
    )

    # Swap algo.
    algo_swap = testbed.pool.prepare_swap(
        asset=testbed.algo,
        amount=20_000,
        slippage_pct=2,
    )
    algo_swap_tx_group = algo_swap.prepare_tx_group(testbed.account.address)
    assert len(algo_swap_tx_group.transactions) == 2
    sign_and_send(algo_swap_tx_group, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary > 100_000
    assert testbed.pool.state.total_secondary < 100_000
    assert testbed.pool.state.primary_asset_price < 1
    assert testbed.pool.state.secondary_asset_price > 1

    # Swap secondary.
    coin_swap = testbed.pool.prepare_swap(
        asset=testbed.coin,
        amount=50_000,
        slippage_pct=2,
    )
    coin_swap_tx = coin_swap.prepare_tx_group(testbed.account.address)
    sign_and_send(coin_swap_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary < 100_000
    assert testbed.pool.state.total_secondary > 100_000
    assert testbed.pool.state.primary_asset_price > 1
    assert testbed.pool.state.secondary_asset_price < 1


def test_constant_product_pool_parsing_state(testbed: TestBed):
    state = {
        "A": 0,
        "ADMIN": testbed.account.address,
        "ASSET_A": testbed.pool.primary_asset.index,
        "ASSET_B": testbed.pool.secondary_asset.index,
        "LTID": testbed.pool.liquidity_asset.index,
        "B": 0,
        "CONTRACT_NAME": "PACT AMM",
        "FEE_BPS": testbed.pool.fee_bps,
        "L": 0,
        "PACT_FEE_BPS": 0,
        "PRIMARY_FEES": 0,
        "SECONDARY_FEES": 0,
        "TREASURY": testbed.account.address,
        "VERSION": 2,
        "FUTURE_A": None,
        "FUTURE_ADMIN": None,
        "FUTURE_A_TIME": None,
        "INITIAL_A": None,
        "INITIAL_A_TIME": None,
        "PRECISION": None,
    }
    __base_pool_parsing_state(testbed, state)


def test_constant_product_v_1_pool_parsing_state(testbed_v_1: TestBed):
    testbed = testbed_v_1
    state = {
        "A": 0,
        "ADMIN": None,
        "ASSET_A": testbed.pool.primary_asset.index,
        "ASSET_B": testbed.pool.secondary_asset.index,
        "LTID": testbed.pool.liquidity_asset.index,
        "B": 0,
        "CONTRACT_NAME": None,
        "FEE_BPS": testbed.pool.fee_bps,
        "L": 0,
        "PACT_FEE_BPS": None,
        "PRIMARY_FEES": None,
        "SECONDARY_FEES": None,
        "TREASURY": None,
        "VERSION": None,
        "FUTURE_A": None,
        "FUTURE_ADMIN": None,
        "FUTURE_A_TIME": None,
        "INITIAL_A": None,
        "INITIAL_A_TIME": None,
        "PRECISION": None,
    }
    __base_pool_parsing_state(testbed, state, 0)


def __base_pool_parsing_state(testbed: TestBed, state: dict, version: int = 2):
    assert testbed.pool.primary_asset.index == testbed.algo.index
    assert testbed.pool.secondary_asset.index == testbed.coin.index

    assert testbed.pool.pool_type == "CONSTANT_PRODUCT"
    assert testbed.pool.version == version

    assert asdict(testbed.pool.internal_state) == state
