from dataclasses import asdict
from typing import cast

import pactsdk
from pactsdk.client import PactClient
from pactsdk.stableswap_calculator import StableswapParams

from .matchers import Any
from .utils import (
    algod,
    create_asset,
    deploy_stableswap_contract,
    make_fresh_testbed,
    new_account,
    sign_and_send,
)


def test_stableswap_pool_e2e_scenario():
    account = new_account()
    pact = PactClient(algod)

    coin_a_index = create_asset(account, "COIN_A", 6, 10**10)
    coin_b_index = create_asset(account, "COIN_B", 6, 10**10)

    coin_a = pact.fetch_asset(coin_a_index)
    coin_b = pact.fetch_asset(coin_b_index)

    app_id = deploy_stableswap_contract(
        account, coin_a_index, coin_b_index, amplifier=20, fee_bps=60
    )
    pool = pact.fetch_pool_by_id(app_id)

    assert pool.state == pactsdk.PoolState(
        total_liquidity=0,
        total_primary=0,
        total_secondary=0,
        primary_asset_price=0,
        secondary_asset_price=0,
    )

    # Opt in for liquidity asset.
    liq_opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(account.address)
    sign_and_send(liq_opt_in_tx, account)

    # Add liquidity.
    liquidity_addition = pool.prepare_add_liquidity(
        primary_asset_amount=100_000_000,
        secondary_asset_amount=100_000_000,
    )
    add_liq_tx_group = liquidity_addition.prepare_tx_group(address=account.address)
    assert add_liq_tx_group.group_id
    assert len(add_liq_tx_group.transactions) == 3
    sign_and_send(add_liq_tx_group, account)
    pool.update_state()
    assert pool.state == pactsdk.PoolState(
        total_liquidity=100_000_000,
        total_primary=100_000_000,
        total_secondary=100_000_000,
        primary_asset_price=Any(float),
        secondary_asset_price=Any(float),
    )
    assert f"{pool.state.primary_asset_price:.2f}" == "1.00"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.00"

    # Remove liquidity.
    remove_liq_tx_group = pool.prepare_remove_liquidity_tx_group(
        address=account.address,
        amount=1_000_000,
    )
    assert len(remove_liq_tx_group.transactions) == 2
    sign_and_send(remove_liq_tx_group, account)
    pool.update_state()
    assert pool.state == pactsdk.PoolState(
        total_liquidity=99_000_000,
        total_primary=99_000_000,
        total_secondary=99_000_000,
        primary_asset_price=Any(float),
        secondary_asset_price=Any(float),
    )
    assert f"{pool.state.primary_asset_price:.2f}" == "1.00"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.00"

    # Swap coin a.
    coin_a_swap = pool.prepare_swap(
        asset=coin_a,
        amount=2_000_000,
        slippage_pct=2,
    )
    algo_swap_tx_group = coin_a_swap.prepare_tx_group(account.address)
    assert len(algo_swap_tx_group.transactions) == 2
    sign_and_send(algo_swap_tx_group, account)
    pool.update_state()
    assert pool.state.total_liquidity == 99_000_000
    assert pool.state.total_primary > 99_000_000
    assert pool.state.total_secondary < 99_000_000
    assert f"{pool.state.primary_asset_price:.2f}" == "1.00"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.00"

    # Swap coin b.
    coin_b_swap = pool.prepare_swap(
        asset=coin_b,
        amount=5_000_000,
        slippage_pct=2,
    )
    coin_swap_tx = coin_b_swap.prepare_tx_group(account.address)
    sign_and_send(coin_swap_tx, account)
    pool.update_state()
    assert pool.state.total_liquidity == 99_000_000
    assert pool.state.total_primary < 99_000_000
    assert pool.state.total_secondary > 99_000_000
    assert f"{pool.state.primary_asset_price:.2f}" == "1.00"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.00"

    # Only big swaps should affect the price.
    big_coin_b_swap = pool.prepare_swap(
        asset=coin_b,
        amount=90_000_000,
        slippage_pct=2,
    )
    coin_swap_tx = big_coin_b_swap.prepare_tx_group(account.address)
    sign_and_send(coin_swap_tx, account)
    pool.update_state()
    assert pool.state.total_liquidity == 99_000_000
    assert pool.state.total_primary < 99_000_000
    assert pool.state.total_secondary > 99_000_000
    assert f"{pool.state.primary_asset_price:.2f}" == "1.61"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.62"

    a_precision = 1000

    # Check different amplifiers.
    pool_params = cast(StableswapParams, pool.params)
    pool_params.future_a = 1
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "13.97"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.07"

    pool_params.future_a = a_precision
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "5.15"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.20"

    pool_params.future_a = 5 * a_precision
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "2.78"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.36"

    pool_params.future_a = 100 * a_precision
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "1.14"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.88"

    pool_params.future_a = 1000 * a_precision
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "1.01"
    assert f"{pool.state.secondary_asset_price:.2f}" == "0.99"


def test_stableswap_pool_parsing_state():
    testbed = make_fresh_testbed("STABLESWAP")

    assert testbed.pool.primary_asset.index == testbed.algo.index
    assert testbed.pool.secondary_asset.index == testbed.coin.index

    assert testbed.pool.pool_type == "STABLESWAP"
    assert testbed.pool.version == 1

    timestamp = testbed.pool.internal_state.INITIAL_A_TIME

    assert asdict(testbed.pool.internal_state) == {
        "A": 0,
        "ADMIN": testbed.account.address,
        "ASSET_A": testbed.pool.primary_asset.index,
        "ASSET_B": testbed.pool.secondary_asset.index,
        "LTID": testbed.pool.liquidity_asset.index,
        "B": 0,
        "CONTRACT_NAME": "[SI] PACT AMM",
        "FEE_BPS": testbed.pool.fee_bps,
        "L": 0,
        "PACT_FEE_BPS": 0,
        "PRIMARY_FEES": 0,
        "SECONDARY_FEES": 0,
        "TREASURY": testbed.account.address,
        "VERSION": 1,
        "INITIAL_A": 80000,
        "INITIAL_A_TIME": timestamp,
        "FUTURE_A": 80000,
        "FUTURE_A_TIME": timestamp,
        "PRECISION": 1000,
        "FUTURE_ADMIN": None,
    }
