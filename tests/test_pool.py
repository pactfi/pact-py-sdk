from decimal import Decimal as D

import pytest
import responses

import pactsdk

from .utils import TestBed, algod, sign_and_send


@responses.activate
def test_listing_pools():
    pact = pactsdk.PactClient(algod)

    mocked_api_data: dict = {
        "results": [
            {
                "appid": 2,
                "primary_asset": 0,
                "secondary_asset": 1,
            },
        ],
    }

    responses.add(
        responses.GET,
        f"{pact.pact_api_url}/api/pools",
        json=mocked_api_data,
    )

    pools = pact.list_pools()
    assert pools == mocked_api_data


@responses.activate
def test_fetching_pool_from_api(testbed: TestBed):
    mocked_api_data: dict = {
        "results": [
            {
                "appid": testbed.pool.app_id,
                "primary_asset": testbed.pool.primary_asset.index,
                "secondary_asset": testbed.pool.secondary_asset.index,
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pool = pact.fetch_pool(testbed.algo, testbed.coin)

    assert pool.primary_asset.index == testbed.algo.index
    assert pool.secondary_asset.index == testbed.coin.index
    assert pool.liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pool.liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pool.app_id == testbed.pool.app_id


@responses.activate
def test_fetching_not_existing_pool_from_api(testbed: TestBed):
    mocked_api_data: dict = {"results": []}  # no pool returned

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.pact_api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    with pytest.raises(
        pactsdk.PactSdkError,
        match=f"Cannot find pool for assets 0 and {testbed.coin.index}",
    ):
        pact.fetch_pool(testbed.algo, testbed.coin)


def test_fetching_pool_by_providing_app_id(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    pool = pact.fetch_pool(
        testbed.algo,
        testbed.coin,
        app_id=testbed.pool.app_id,
    )

    assert pool.primary_asset.index == testbed.algo.index
    assert pool.secondary_asset.index == testbed.coin.index
    assert pool.liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pool.liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pool.app_id == testbed.pool.app_id


def test_fetching_pool_with_reversed_assets(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    # We reverse the assets order here.
    pool = pact.fetch_pool(
        testbed.coin,
        testbed.algo,
        app_id=testbed.pool.app_id,
    )

    assert pool.primary_asset.index == testbed.algo.index
    assert pool.secondary_asset.index == testbed.coin.index
    assert pool.liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pool.liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pool.app_id == testbed.pool.app_id


def test_pool_get_other_other(testbed: TestBed):
    assert testbed.pool.get_other_asset(testbed.algo) == testbed.coin
    assert testbed.pool.get_other_asset(testbed.coin) == testbed.algo

    shitcoin = pactsdk.Asset(
        algod=testbed.pact.algod, index=testbed.coin.index + 1, decimals=0
    )
    with pytest.raises(
        pactsdk.PactSdkError,
        match=f"Asset with index {shitcoin.index} is not a pool asset.",
    ):
        testbed.pool.get_other_asset(shitcoin)


def test_pool_e2e_scenario(testbed: TestBed):
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=0,
        total_primary=0,
        total_secondary=0,
        primary_asset_price=D(0),
        secondary_asset_price=D(0),
    )

    # Opt in for liquidity asset.
    liq_opt_in_tx = testbed.pool.liquidity_asset.prepare_opt_in_tx(
        testbed.account.address
    )
    sign_and_send(liq_opt_in_tx, testbed.account)

    # Add liquidity.
    add_liq_tx = testbed.pool.prepare_add_liquidity_tx(
        address=testbed.account.address,
        primary_asset_amount=100_000,
        secondary_asset_amount=100_000,
    )
    sign_and_send(add_liq_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=100_000,
        total_primary=100_000,
        total_secondary=100_000,
        primary_asset_price=D(1),
        secondary_asset_price=D(1),
    )

    # Remove liquidity.
    remove_liq_tx = testbed.pool.prepare_remove_liquidity_tx(
        address=testbed.account.address,
        amount=10_000,
    )
    sign_and_send(remove_liq_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state == pactsdk.PoolState(
        total_liquidity=90_000,
        total_primary=90_000,
        total_secondary=90_000,
        primary_asset_price=D(1),
        secondary_asset_price=D(1),
    )

    # Swap algo.
    algo_swap = testbed.pool.prepare_swap(
        asset=testbed.algo,
        amount=20_000,
        slippage_pct=2,
    )
    algo_swap_tx = algo_swap.prepare_tx(testbed.account.address)
    sign_and_send(algo_swap_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary > 100_000
    assert testbed.pool.state.total_secondary < 100_000
    assert testbed.pool.state.primary_asset_price < D(1)
    assert testbed.pool.state.secondary_asset_price > D(1)

    # Swap secondary.
    coin_swap = testbed.pool.prepare_swap(
        asset=testbed.coin,
        amount=50_000,
        slippage_pct=2,
    )
    coin_swap_tx = coin_swap.prepare_tx(testbed.account.address)
    sign_and_send(coin_swap_tx, testbed.account)
    testbed.pool.update_state()
    assert testbed.pool.state.total_liquidity == 90_000
    assert testbed.pool.state.total_primary < 100_000
    assert testbed.pool.state.total_secondary > 100_000
    assert testbed.pool.state.primary_asset_price > D(1)
    assert testbed.pool.state.secondary_asset_price < D(1)
