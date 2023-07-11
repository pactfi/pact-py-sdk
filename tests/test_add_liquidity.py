import pytest

from pactsdk import LiquidityAddition
from pactsdk.exceptions import PactSdkError
from pactsdk.pool import Pool, PoolType
from tests.pool_utils import POOL_TYPES, add_liquidity, make_fresh_testbed
from tests.utils import Account, sign_and_send


def assert_add_liquidity(
    liquidity_addition: LiquidityAddition,
    account: Account,
):
    # Perform adding liquidity.
    old_state = liquidity_addition.pool.state
    swap_tx_group = liquidity_addition.prepare_tx_group(account.address)
    sign_and_send(swap_tx_group, account)
    liquidity_addition.pool.update_state()

    # Compare the simulated effect with what really happened on the blockchain.
    new_state = liquidity_addition.pool.state
    minted_tokens = new_state.total_liquidity - old_state.total_liquidity

    assert liquidity_addition.effect.minted_liquidity_tokens == (minted_tokens)


def assert_stableswap_bonus(
    pool: Pool,
    account: Account,
    liquidity_addition: LiquidityAddition,
):
    # Removes liquidity, calculates a real bonus and compares it with a simulation.
    old_state = pool.state

    remove_liquidity_group = pool.prepare_remove_liquidity_tx_group(
        address=account.address,
        amount=liquidity_addition.effect.minted_liquidity_tokens,
    )
    sign_and_send(remove_liquidity_group, account)

    pool.update_state()
    new_state = pool.state

    received = (
        old_state.total_primary
        - new_state.total_primary
        + (old_state.total_secondary - new_state.total_secondary)
    )

    total_added = (
        liquidity_addition.primary_asset_amount
        + liquidity_addition.secondary_asset_amount
    )
    real_bonus_pct = ((received - total_added) / total_added) * 100

    assert f"{liquidity_addition.effect.bonus_pct:.1f}" == f"{real_bonus_pct:.1f}"


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_add_liquidity_with_empty_pool_add_equal_liquidity(pool_type: PoolType):
    testbed = make_fresh_testbed(pool_type=pool_type)
    primary_asset_amount, secondary_asset_amount = (10_000, 10_000)

    opt_in_tx = testbed.pool.liquidity_asset.prepare_opt_in_tx(testbed.account.address)
    sign_and_send(opt_in_tx, testbed.account)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_add_liquidity_empty_pool_add_not_equal_liquidity(pool_type: PoolType):
    testbed = make_fresh_testbed(pool_type=pool_type)
    primary_asset_amount, secondary_asset_amount = (30_000, 10_000)

    opt_in_tx = testbed.pool.liquidity_asset.prepare_opt_in_tx(testbed.account.address)
    sign_and_send(opt_in_tx, testbed.account)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_add_liquiidty_not_an_empty_pool_add_equal_liquidity(pool_type: PoolType):
    testbed = make_fresh_testbed(pool_type=pool_type)

    add_liquidity(testbed.account, testbed.pool, 50_000, 60_000)

    primary_asset_amount, secondary_asset_amount = (10_000, 10_000)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)


@pytest.mark.parametrize("pool_type", POOL_TYPES)
def test_add_liquidity_not_an_empty_pool_add_not_equal_liquidity(pool_type: PoolType):
    testbed = make_fresh_testbed(pool_type=pool_type)

    add_liquidity(testbed.account, testbed.pool, 50_000, 60_000)

    primary_asset_amount, secondary_asset_amount = (30_000, 10_000)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)


def test_add_liquidity_stableswap_add_only_primary_asset():
    testbed = make_fresh_testbed(pool_type="STABLESWAP")

    add_liquidity(testbed.account, testbed.pool, 50_000, 60_000)

    primary_asset_amount, secondary_asset_amount = (30_000, 0)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)


def test_add_liquidity_stableswap_add_only_secondary_asset():
    testbed = make_fresh_testbed(
        pool_type="STABLESWAP",
    )

    add_liquidity(testbed.account, testbed.pool, 50_000, 60_000)

    primary_asset_amount, secondary_asset_amount = (0, 10_000)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)
    assert_stableswap_bonus(testbed.pool, testbed.account, liquidity_addition)

    assert liquidity_addition.effect.bonus_pct < 0


def test_add_liquidity_stableswap_add_with_a_positive_bonus():
    testbed = make_fresh_testbed(pool_type="STABLESWAP")

    add_liquidity(testbed.account, testbed.pool, 10_000, 60_000)

    primary_asset_amount, secondary_asset_amount = (50_000, 0)

    liquidity_addition = testbed.pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
        slippage_pct=0,
    )

    assert_add_liquidity(liquidity_addition, testbed.account)
    assert_stableswap_bonus(testbed.pool, testbed.account, liquidity_addition)

    assert liquidity_addition.effect.bonus_pct > 0


def test_add_liquidity_stableswap_pool_liquidity_too_low_to_cover_fee():
    testbed = make_fresh_testbed(
        pool_type="STABLESWAP",
        fee_bps=1000,
    )

    add_liquidity(testbed.account, testbed.pool, 1000, 100_000)

    primary_asset_amount, secondary_asset_amount = (0, 1_000_000_000)

    # "pool liquidity too low to cover add liquidity fee."
    with pytest.raises(PactSdkError):
        testbed.pool.prepare_add_liquidity(
            primary_asset_amount=primary_asset_amount,
            secondary_asset_amount=secondary_asset_amount,
            slippage_pct=0,
        )
