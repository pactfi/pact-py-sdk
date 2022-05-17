from typing import cast

import pactsdk
from pactsdk.client import PactClient
from pactsdk.stableswap_calculator import StableswapParams

from .matchers import Any
from .utils import (
    algod,
    create_asset,
    deploy_stableswap_contract,
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
        account, coin_a_index, coin_b_index, amplifier=20
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
    add_liq_tx_group = pool.prepare_add_liquidity_tx_group(
        address=account.address,
        primary_asset_amount=100_000_000,
        secondary_asset_amount=100_000_000,
    )
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
    assert f"{pool.state.primary_asset_price:.2f}" == "0.57"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.76"

    # Check different amplifiers.
    pool_params = cast(StableswapParams, pool.params)
    pool_params.future_a = 1
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "0.19"
    assert f"{pool.state.secondary_asset_price:.2f}" == "5.24"

    pool_params.future_a = 1000
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "0.98"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.02"

    pool_params.future_a = 5000
    pool.state = pool.parse_internal_state(pool.internal_state)
    assert f"{pool.state.primary_asset_price:.2f}" == "1.00"
    assert f"{pool.state.secondary_asset_price:.2f}" == "1.00"
