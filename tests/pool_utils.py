from dataclasses import dataclass
from typing import Union

import pactsdk

from .utils import (
    Account,
    algod,
    create_asset,
    deploy_contract,
    new_account,
    sign_and_send,
)

POOL_TYPES: list[pactsdk.pool.PoolType] = ["CONSTANT_PRODUCT", "STABLESWAP"]


def deploy_constant_product_contract(
    account: Account,
    primary_asset_index: int,
    secondary_asset_index: int,
    fee_bps=30,
    pact_fee_bps=0,
):
    return deploy_exchange(
        account,
        "CONSTANT_PRODUCT",
        primary_asset_index,
        secondary_asset_index,
        fee_bps=fee_bps,
        pact_fee_bps=pact_fee_bps,
    )


def deploy_stableswap_contract(
    account: Account,
    primary_asset_index: int,
    secondary_asset_index: int,
    fee_bps=30,
    pact_fee_bps=0,
    amplifier=80,
):
    return deploy_exchange(
        account,
        "STABLESWAP",
        primary_asset_index,
        secondary_asset_index,
        fee_bps=fee_bps,
        pact_fee_bps=pact_fee_bps,
        amplifier=amplifier,
    )


def deploy_exchange(
    account: Account,
    pool_type: str,
    primary_asset_index: int,
    secondary_asset_index: int,
    fee_bps=30,
    pact_fee_bps=0,
    amplifier=80,
    version=None,  # New smart contracts Stableswap and Constant Exchange marked as version 2, old Constant Exchange as version 1.
) -> int:
    command = [
        "exchange",
        f"--contract-type={pool_type.lower()}",
        f"--primary_asset_id={primary_asset_index}",
        f"--secondary_asset_id={secondary_asset_index}",
        f"--fee_bps={fee_bps}",
        f"--pact_fee_bps={pact_fee_bps}",
        f"--amplifier={amplifier * 1000}",
        f"--admin_and_treasury_address={account.address}",
    ]

    if version:
        command.append(f"--version={version}")

    return deploy_contract(account, command)


def add_liquidity(
    account: Account,
    pool: pactsdk.Pool,
    primary_asset_amount=10_000,
    secondary_asset_amount=10_000,
):
    opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(account.address)
    sign_and_send(opt_in_tx, account)

    liquidity_addition = pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
    )
    add_liq_tx_group = liquidity_addition.prepare_tx_group(account.address)
    sign_and_send(add_liq_tx_group, account)
    pool.update_state()


@dataclass
class TestBed:
    __test__ = False

    account: Account
    pact: pactsdk.PactClient
    algo: pactsdk.Asset
    coin: pactsdk.Asset
    pool: pactsdk.Pool


def make_fresh_testbed(
    pool_type: pactsdk.pool.PoolType,
    fee_bps=30,
    amplifier=80,
    version: Union[None, int] = None,
) -> TestBed:
    account = new_account()
    pact = pactsdk.PactClient(algod)

    coin_index = create_asset(account)

    app_id = deploy_exchange(
        pool_type=pool_type,
        account=account,
        primary_asset_index=0,
        secondary_asset_index=coin_index,
        fee_bps=fee_bps,
        amplifier=amplifier,
        version=version,
    )
    pool = pact.fetch_pool_by_id(app_id=app_id)

    return TestBed(
        account=account,
        pact=pact,
        algo=pool.primary_asset,
        coin=pool.secondary_asset,
        pool=pool,
    )


def assert_swap(swap: pactsdk.Swap, account: Account):
    # Perform the swap.
    old_state = swap.pool.state
    swap_tx_group = swap.prepare_tx_group(account.address)
    sign_and_send(swap_tx_group, account)
    swap.pool.update_state()

    # Compare the simulated effect with what really happened on the blockchain.
    assert_pool_state(swap, old_state, swap.pool.state)


def assert_pool_state(
    swap: pactsdk.Swap, old_state: pactsdk.PoolState, new_state: pactsdk.PoolState
):
    if swap.asset_deposited == swap.pool.primary_asset:
        assert (
            swap.effect.amount_deposited
            == new_state.total_primary - old_state.total_primary
        )
        assert (
            swap.effect.amount_received
            == old_state.total_secondary - new_state.total_secondary
        )
    else:
        assert (
            swap.effect.amount_received
            == old_state.total_primary - new_state.total_primary
        )
        assert (
            swap.effect.amount_deposited
            == new_state.total_secondary - old_state.total_secondary
        )

    assert swap.effect.minimum_amount_received == int(
        swap.effect.amount_received
        - swap.effect.amount_received * (swap.slippage_pct / 100)
    )

    diff_ratio = swap.asset_deposited.ratio / swap.asset_received.ratio
    expected_price = (
        (swap.effect.amount_received + swap.effect.fee) / swap.effect.amount_deposited
    ) * diff_ratio
    assert swap.effect.price == expected_price

    assert swap.effect.primary_asset_price_after_swap == new_state.primary_asset_price
    assert (
        swap.effect.secondary_asset_price_after_swap == new_state.secondary_asset_price
    )

    assert swap.effect.primary_asset_price_change_pct == (
        (new_state.primary_asset_price / old_state.primary_asset_price) * 100 - 100
    )
    assert swap.effect.secondary_asset_price_change_pct == (
        (new_state.secondary_asset_price / old_state.secondary_asset_price) * 100 - 100
    )
