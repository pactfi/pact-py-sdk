from dataclasses import asdict

import algosdk
import pytest

import pactsdk

from .factory_utils import deploy_factory
from .utils import Account, algod, create_asset, new_account


@pytest.fixture()
def admin():
    return new_account()


@pytest.fixture()
def pact(admin):
    factory_id = deploy_factory(
        account=admin,
        contract_type="CONSTANT_PRODUCT",
        admin_and_treasury_address=admin.address,
    )
    return pactsdk.PactClient(algod, factory_constant_product_id=factory_id)


@pytest.fixture()
def pact_nft(admin):
    factory_id = deploy_factory(
        account=admin,
        contract_type="NFT_CONSTANT_PRODUCT",
        admin_and_treasury_address=admin.address,
    )
    return pactsdk.PactClient(algod, factory_nft_constant_product_id=factory_id)


def test_factory_deploy_constant_product_pool(pact: pactsdk.PactClient, admin: Account):
    algo = pact.fetch_asset(0)
    coin = pact.fetch_asset(create_asset(admin))

    factory = pact.get_constant_product_pool_factory()

    # Validate fee bps.
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=200
    )
    with pytest.raises(AssertionError) as err:
        pool = factory.build(
            sender=admin.address,
            pool_build_params=pool_build_params,
            signer=lambda tx_group: tx_group.sign(admin.private_key),
        )
    assert "only one of [100, 30, 5, 2] is allowed for fee_bps" in str(err)

    # Build the pool.
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=100
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )

    assert pool.pool_type == "CONSTANT_PRODUCT"
    assert pool.version == 201
    assert pool.primary_asset.index == algo.index
    assert pool.secondary_asset.index == coin.index
    assert pool.fee_bps == 100
    assert pool.params.pact_fee_bps == 10

    # Validate that the pool is functional. Let's add some liquidity.

    opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(admin.address)
    algod.send_transaction(opt_in_tx.sign(admin.private_key))

    liquidity_addition = pool.prepare_add_liquidity(1000, 2000, 0)
    tx_group = pool.prepare_add_liquidity_tx_group(admin.address, liquidity_addition)
    algod.send_transactions(tx_group.sign(admin.private_key))

    pool.update_state()
    assert pool.state.total_primary == 1000
    assert pool.state.total_secondary == 2000


def test_factory_deploy_nft_constant_product_pool(
    pact_nft: pactsdk.PactClient, admin: Account
):
    pact = pact_nft
    algo = pact.fetch_asset(0)
    coin = pact.fetch_asset(create_asset(admin, total=1_000, decimals=3))

    factory = pact.get_nft_constant_product_pool_factory()

    # Validate fee
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=100
    )
    with pytest.raises(AssertionError) as err:
        pool = factory.build(
            sender=admin.address,
            pool_build_params=pool_build_params,
            signer=lambda tx_group: tx_group.sign(admin.private_key),
        )
    assert "only one of [350] is allowed for fee_bps" in str(err)

    # Build the pool.
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=350
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )

    assert pool.pool_type == "NFT_CONSTANT_PRODUCT"
    assert pool.version == 201
    assert pool.primary_asset.index == algo.index
    assert pool.secondary_asset.index == coin.index
    assert pool.fee_bps == 350
    assert pool.params.pact_fee_bps == 170

    # Validate that the pool is functional. Let's add some liquidity.

    opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(admin.address)
    algod.send_transaction(opt_in_tx.sign(admin.private_key))

    liquidity_addition = pool.prepare_add_liquidity(10_000, 500, 0)
    tx_group = pool.prepare_add_liquidity_tx_group(admin.address, liquidity_addition)
    algod.send_transactions(tx_group.sign(admin.private_key))

    pool.update_state()
    assert pool.state.total_primary == 10_000
    assert pool.state.total_secondary == 500


def test_factory_deploy_pool_as_normal_user(pact: pactsdk.PactClient, admin: Account):
    user = new_account()
    algo = pact.fetch_asset(0)
    coin = pact.fetch_asset(create_asset(admin))

    factory = pact.get_constant_product_pool_factory()
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=100
    )
    pool = factory.build(
        sender=user.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(user.private_key),
    )

    assert pool.pool_type == "CONSTANT_PRODUCT"
    assert pool.version == 201


def test_factory_deploy_constant_product_pool_with_different_params_and_listing_pools(
    pact: pactsdk.PactClient, admin: Account
):
    algo = pact.fetch_asset(0)
    coin_a = pact.fetch_asset(create_asset(admin))
    coin_b = pact.fetch_asset(create_asset(admin))

    factory = pact.get_constant_product_pool_factory()

    # ALGO/COIN_A 0.02%
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin_a.index, fee_bps=2
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert pool.primary_asset.index == algo.index
    assert pool.secondary_asset.index == coin_a.index
    assert pool.fee_bps == 2
    assert pool.params.pact_fee_bps == 1

    # ALGO/COIN_A 0.05%
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin_a.index, fee_bps=5
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert pool.primary_asset.index == algo.index
    assert pool.secondary_asset.index == coin_a.index
    assert pool.fee_bps == 5
    assert pool.params.pact_fee_bps == 2

    # ALGO/COIN_A 0.3%
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin_a.index, fee_bps=30
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert pool.primary_asset.index == algo.index
    assert pool.secondary_asset.index == coin_a.index
    assert pool.fee_bps == 30
    assert pool.params.pact_fee_bps == 5

    # COIN_A/COIN_B 0.05%
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=coin_a.index, secondary_asset_id=coin_b.index, fee_bps=5
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert pool.primary_asset.index == coin_a.index
    assert pool.secondary_asset.index == coin_b.index
    assert pool.fee_bps == 5
    assert pool.params.pact_fee_bps == 2

    pool_version = pool.version
    # Cannot create a second pool with the same params.
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=coin_a.index, secondary_asset_id=coin_b.index, fee_bps=5
    )
    with pytest.raises(algosdk.error.AlgodHTTPError):
        pool = factory.build(
            sender=admin.address,
            pool_build_params=pool_build_params,
            signer=lambda tx_group: tx_group.sign(admin.private_key),
        )

    # Forbidden fee.
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=coin_a.index, secondary_asset_id=coin_b.index, fee_bps=200
    )
    with pytest.raises(AssertionError):
        pool = factory.build(
            sender=admin.address,
            pool_build_params=pool_build_params,
            signer=lambda tx_group: tx_group.sign(admin.private_key),
        )

    # List the pools.
    pools = factory.list_pools()
    assert set(pools) == {
        pactsdk.PoolParams(
            primary_asset_id=algo.index,
            secondary_asset_id=coin_a.index,
            fee_bps=2,
            version=pool_version,
        ),
        pactsdk.PoolParams(
            primary_asset_id=algo.index,
            secondary_asset_id=coin_a.index,
            fee_bps=5,
            version=pool_version,
        ),
        pactsdk.PoolParams(
            primary_asset_id=algo.index,
            secondary_asset_id=coin_a.index,
            fee_bps=30,
            version=pool_version,
        ),
        pactsdk.PoolParams(
            primary_asset_id=coin_a.index,
            secondary_asset_id=coin_b.index,
            fee_bps=5,
            version=pool_version,
        ),
    }


def test_factory_fetch_pool(pact: pactsdk.PactClient, admin: Account):
    algo = pact.fetch_asset(0)
    coin = pact.fetch_asset(create_asset(admin))

    factory = pact.get_constant_product_pool_factory()

    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=100
    )
    pool = factory.build(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    pool_params = pactsdk.PoolParams(**asdict(pool_build_params), version=pool.version)
    assert factory.fetch_pool(pool_params) == pool

    pool_params = pactsdk.PoolParams(
        primary_asset_id=algo.index,
        secondary_asset_id=coin.index,
        fee_bps=30,
        version=pool.version,
    )
    assert factory.fetch_pool(pool_params) is None


def test_factory_build_or_get(pact: pactsdk.PactClient, admin: Account):
    algo = pact.fetch_asset(0)
    coin = pact.fetch_asset(create_asset(admin))

    factory = pact.get_constant_product_pool_factory()
    pool_build_params = pactsdk.PoolBuildParams(
        primary_asset_id=algo.index, secondary_asset_id=coin.index, fee_bps=100
    )

    # Create the pool.
    pool, created = factory.build_or_get(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert created is True
    assert pool.pool_type == "CONSTANT_PRODUCT"

    # Try to create a second pool.
    another_pool, created = factory.build_or_get(
        sender=admin.address,
        pool_build_params=pool_build_params,
        signer=lambda tx_group: tx_group.sign(admin.private_key),
    )
    assert created is False
    assert another_pool == pool
