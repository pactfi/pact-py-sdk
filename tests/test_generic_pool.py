import algosdk
import pytest
import responses

import pactsdk
from pactsdk.client import PactClient

from .pool_utils import TestBed, deploy_constant_product_contract, deploy_exchange
from .utils import algod, create_asset, new_account, sign_and_send


@responses.activate
def test_listing_pools():
    pact = pactsdk.PactClient(algod)

    mocked_api_data: dict = {
        "results": [
            {
                "appid": "2",
                "primary_asset": {"algoid": "0"},
                "secondary_asset": {"algoid": "1"},
            },
        ],
    }

    responses.add(
        responses.GET,
        f"{pact.config.api_url}/api/pools",
        json=mocked_api_data,
    )

    pools = pact.list_pools()
    assert pools == mocked_api_data


@responses.activate
def test_fetching_pools_by_assets(testbed: TestBed):
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.config.api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)

    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id

    assert pools[0].get_escrow_address()

    # Can fetch by ids.
    pools = pact.fetch_pools_by_assets(testbed.algo.index, testbed.coin.index)
    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index


@responses.activate
def test_fetching_pools_by_assets_with_reversed_assets(testbed: TestBed):
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.config.api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    # We reverse the assets order here.
    pools = pact.fetch_pools_by_assets(testbed.coin, testbed.algo)

    assert len(pools) == 1
    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id


@responses.activate
def test_fetching_pools_by_assets_multiple_results(testbed: TestBed):
    second_app_id = deploy_constant_product_contract(
        testbed.account,
        testbed.algo.index,
        testbed.coin.index,
        fee_bps=100,
    )
    mocked_api_data: dict = {
        "results": [
            {
                "appid": str(testbed.pool.app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
            {
                "appid": str(second_app_id),
                "primary_asset": {
                    "algoid": str(testbed.pool.primary_asset.index),
                },
                "secondary_asset": {
                    "algoid": str(testbed.pool.secondary_asset.index),
                },
            },
        ],
    }

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.config.api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)

    assert len(pools) == 2

    assert pools[0].primary_asset.index == testbed.algo.index
    assert pools[0].secondary_asset.index == testbed.coin.index
    assert pools[0].liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pools[0].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[0].app_id == testbed.pool.app_id
    assert pools[0].fee_bps == 30

    assert pools[1].primary_asset.index == testbed.algo.index
    assert pools[1].secondary_asset.index == testbed.coin.index
    assert pools[1].liquidity_asset.index != testbed.pool.liquidity_asset.index
    assert pools[1].liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pools[1].app_id == second_app_id
    assert pools[1].fee_bps == 100


@responses.activate
def test_fetching_pools_by_assets_not_existing_pool(testbed: TestBed):
    mocked_api_data: dict = {"results": []}  # no pool returned

    qs_params = {
        "primary_asset__algoid": str(testbed.pool.primary_asset.index),
        "secondary_asset__algoid": str(testbed.pool.secondary_asset.index),
    }

    responses.add(
        responses.GET,
        f"{testbed.pact.config.api_url}/api/pools",
        match=[responses.matchers.query_param_matcher(qs_params)],
        json=mocked_api_data,
    )

    pact = pactsdk.PactClient(algod)

    pools = pact.fetch_pools_by_assets(testbed.algo, testbed.coin)
    assert pools == []


def test_fetching_pools_by_id(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    pool = pact.fetch_pool_by_id(app_id=testbed.pool.app_id)

    assert pool.primary_asset.index == testbed.algo.index
    assert pool.secondary_asset.index == testbed.coin.index
    assert pool.liquidity_asset.index == testbed.pool.liquidity_asset.index
    assert pool.liquidity_asset.name == "ALGO/COIN PACT LP Token"
    assert pool.app_id == testbed.pool.app_id


def test_fetching_pools_by_id_not_existing(testbed: TestBed):
    pact = pactsdk.PactClient(algod)

    with pytest.raises(
        algosdk.error.AlgodHTTPError, match="application does not exist"
    ):
        pact.fetch_pool_by_id(app_id=9999999)


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


def test_adding_big_liquidity_to_an_empty_pool_using_split():
    account = new_account()
    pact = PactClient(algod)

    coin_a_index = create_asset(account, "coinA", 0, 2**50 - 1)
    coin_b_index = create_asset(account, "coinB", 0, 2**50 - 1)

    app_id = deploy_exchange(account, "CONSTANT_PRODUCT", coin_a_index, coin_b_index)
    pool = pact.fetch_pool_by_id(app_id)

    assert pool.pool_type == "CONSTANT_PRODUCT"
    assert pool.calculator.is_empty

    liq_opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(account.address)
    sign_and_send(liq_opt_in_tx, account)

    # Adding initial liquidity has a limitation that the product of 2 assets must be lower than 2**64.
    # Let's go beyond that limit and check what happens.
    [primary_asset_amount, secondary_asset_amount] = [2**40, 2**30]

    liquidity_addition = pool.prepare_add_liquidity(
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
    )
    tx_group = liquidity_addition.prepare_tx_group(address=account.address)

    # liquidity is split into two chunks, so 6 txs instead of 3.
    assert len(tx_group.transactions) == 6

    sign_and_send(tx_group, account)

    pool.update_state()
    assert pool.state.total_primary == primary_asset_amount
    assert pool.state.total_secondary == secondary_asset_amount
