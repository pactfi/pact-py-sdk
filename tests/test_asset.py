import algosdk
import pytest

import pactsdk

from .utils import algod, create_asset, new_account, sign_and_send


def test_fetch_algo():
    pact = pactsdk.PactClient(algod)
    asset = pact.fetch_asset(0)

    assert asset.decimals == 6
    assert asset.index == 0
    assert asset.name == "Algo"
    assert asset.unit_name == "ALGO"
    assert asset.ratio == 10**6


def test_fetch_asa():
    pact = pactsdk.PactClient(algod)
    account = new_account()
    asset_index = create_asset(account, "JAMNIK", 10)
    asset = pact.fetch_asset(asset_index)

    assert asset.decimals == 10
    assert asset.index == asset_index
    assert asset.name == "JAMNIK"
    assert asset.unit_name == "JAMNIK"
    assert asset.ratio == 10**10


def test_fetch_asa_with_no_name():
    pact = pactsdk.PactClient(algod)
    account = new_account()
    asset_index = create_asset(account, name=None, decimals=10)
    asset = pact.fetch_asset(asset_index)

    assert asset.decimals == 10
    assert asset.index == asset_index
    assert asset.name is None
    assert asset.unit_name is None
    assert asset.ratio == 10**10


def test_fetch_not_existing_asset():
    pact = pactsdk.PactClient(algod)

    with pytest.raises(algosdk.error.AlgodHTTPError, match="asset does not exist"):
        pact.fetch_asset(99999999)


def test_opt_in_for_an_asset():
    pact = pactsdk.PactClient(algod)
    creator = new_account()
    assetIndex = create_asset(creator, "test", 10)
    asset = pact.fetch_asset(assetIndex)

    user = new_account()
    assert asset.is_opted_in(user.address) is False

    opt_in_tx = asset.prepare_opt_in_tx(user.address)
    sign_and_send(opt_in_tx, user)

    assert asset.is_opted_in(user.address) is True
