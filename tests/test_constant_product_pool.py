import pactsdk

from .utils import TestBed, sign_and_send


def test_constant_product_pool_e2e_scenario(testbed: TestBed):
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
    add_liq_tx_group = testbed.pool.prepare_add_liquidity_tx_group(
        address=testbed.account.address,
        primary_asset_amount=100_000,
        secondary_asset_amount=100_000,
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
