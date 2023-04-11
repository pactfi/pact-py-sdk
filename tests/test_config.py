import pactsdk
from pactsdk.config import Config

from .utils import algod


def test_client_config():
    pact = pactsdk.PactClient(algod)
    assert pact.config == Config(
        api_url="https://api.pact.fi",
        gas_station_id=1027956681,
        factory_constant_product_id=1072843805,
        factory_nft_constant_product_id=1076423760,
    )
    assert pactsdk.get_gas_station().app_id == 1027956681

    pact = pactsdk.PactClient(algod, network="mainnet")
    assert pact.config == Config(
        api_url="https://api.pact.fi",
        gas_station_id=1027956681,
        factory_constant_product_id=1072843805,
        factory_nft_constant_product_id=1076423760,
    )

    pact = pactsdk.PactClient(algod, network="testnet")
    assert pact.config == Config(
        api_url="https://api.testnet.pact.fi",
        gas_station_id=156575978,
        factory_constant_product_id=166540424,
        factory_nft_constant_product_id=166540708,
    )

    pact = pactsdk.PactClient(algod, network="dev")
    assert pact.config == Config(
        api_url="",
        gas_station_id=0,
        factory_constant_product_id=0,
        factory_nft_constant_product_id=0,
    )

    pact = pactsdk.PactClient(algod, api_url="overwritten_url")
    assert pact.config == Config(
        api_url="overwritten_url",
        gas_station_id=1027956681,
        factory_constant_product_id=1072843805,
        factory_nft_constant_product_id=1076423760,
    )

    pact = pactsdk.PactClient(algod, network="dev", factory_constant_product_id=123)
    assert pact.config == Config(
        api_url="",
        gas_station_id=0,
        factory_constant_product_id=123,
        factory_nft_constant_product_id=0,
    )
