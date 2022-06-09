import pactsdk

from .utils import (
    add_liquidity,
    algod,
    assert_swap,
    create_asset,
    deploy_contract,
    new_account,
)


def test_constant_product_swap_asa_to_asa():
    account = new_account()
    pact = pactsdk.PactClient(algod)

    coin_a_index = create_asset(account, "COIN_A", 3)
    coin_b_index = create_asset(account, "COIN_B", 2)

    app_id = deploy_contract(account, "CONSTANT_PRODUCT", coin_a_index, coin_b_index)
    pool = pact.fetch_pool_by_id(app_id=app_id)

    add_liquidity(account, pool, 20_000, 20_000)
    pool.update_state()

    assert pool.state == pactsdk.PoolState(
        total_liquidity=20_000,
        total_primary=20_000,
        total_secondary=20_000,
        primary_asset_price=10,  # because different decimal places for both assets.
        secondary_asset_price=0.1,
    )

    swap = pool.prepare_swap(
        amount=1000,
        asset=pool.primary_asset,
        slippage_pct=10,
    )
    assert_swap(swap, account)
