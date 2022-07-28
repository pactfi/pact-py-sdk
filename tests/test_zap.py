import pytest

import pactsdk

from .utils import (
    add_liquidity,
    algod,
    create_asset,
    make_fresh_testbed,
    new_account,
    sign_and_send,
)


def test_calculate_zap_params():
    testbed = make_fresh_testbed("CONSTANT_PRODUCT")

    add_liquidity(testbed.account, testbed.pool, 100_000, 100_000)
    testbed.pool.update_state()

    # Perform a zap using primary asset.
    zap_primary_add = testbed.pool.prepare_zap(testbed.pool.primary_asset, 10_000, 2)
    assert zap_primary_add.params == pactsdk.ZapParams(
        swap_deposited=4888,
        primary_add_liq=5112,
        secondary_add_liq=4646,
    )

    #  Perform a zap using secondary asset.
    zap_secondary_add = testbed.pool.prepare_zap(
        testbed.pool.secondary_asset, 10_000, 2
    )
    assert zap_secondary_add.params == pactsdk.ZapParams(
        swap_deposited=4888,
        primary_add_liq=4646,
        secondary_add_liq=5112,
    )

    # Perform a zap on unbalanced pool.
    testbed2 = make_fresh_testbed("CONSTANT_PRODUCT")
    add_liquidity(testbed2.account, testbed2.pool, 100_000, 10_000)
    testbed2.pool.update_state()

    ubalanced_zap = testbed2.pool.prepare_zap(testbed2.pool.secondary_asset, 20_000, 2)
    assert ubalanced_zap.params == pactsdk.ZapParams(
        swap_deposited=7339,
        primary_add_liq=42199,
        secondary_add_liq=12661,
    )


def test_pools_and_assets_validation():
    # Zap should not be possible on Stableswaps.
    testbed = make_fresh_testbed("STABLESWAP")
    with pytest.raises(
        AssertionError, match="Zap can only be made on constant product pools."
    ):
        testbed.pool.prepare_zap(
            amount=10_000,
            asset=testbed.pool.primary_asset,
            slippage_pct=1,
        )

    # Zap should throw an error when wrong asset is passed.
    account = new_account()
    pact = pactsdk.PactClient(algod)
    testbed2 = make_fresh_testbed("CONSTANT_PRODUCT")
    coin_x_index = create_asset(account, "COIN_X", 6)
    coin_x = pact.fetch_asset(coin_x_index)
    with pytest.raises(
        AssertionError, match="Provided asset was not found in the pool."
    ):
        testbed2.pool.prepare_zap(
            amount=1_000,
            asset=coin_x,
            slippage_pct=1,
        )

    # Zap should not be possible on empty pools.
    testbed3 = make_fresh_testbed("CONSTANT_PRODUCT")
    with pytest.raises(ValueError, match="Cannot create a Zap on empty pool."):
        testbed3.pool.prepare_zap(
            amount=1_000,
            asset=testbed3.pool.primary_asset,
            slippage_pct=1,
        )


def test_zap_e2e():
    testbed = make_fresh_testbed("CONSTANT_PRODUCT")

    add_liquidity(testbed.account, testbed.pool, 100_000, 100_000)
    testbed.pool.update_state()

    zap_amount = 10_000
    zap = testbed.pool.prepare_zap(testbed.pool.primary_asset, zap_amount, 2)
    assert zap.params.swap_deposited + zap.params.primary_add_liq == zap_amount

    zap_tx_group = zap.prepare_tx_group(testbed.account.address)
    assert len(zap_tx_group.transactions) == 5
    sign_and_send(zap_tx_group, testbed.account)
    testbed.pool.update_state()

    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=104872,
        total_primary=109999,
        total_secondary=100000,
        primary_asset_price=0.9090991736288512,
        secondary_asset_price=1.09999,
    )
