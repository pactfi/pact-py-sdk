import dataclasses
from typing import Literal

CONSTANT_PRODUCT_FEE_BPS = [2, 5, 30, 100]

MAINNET_API_URL = "https://api.pact.fi"
MAINNET_GAS_STATION_ID = 1027956681
MAINNET_FACTORY_CONSTANT_PRODUCT_ID = 0

TESTNET_API_URL = "https://api.testnet.pact.fi"
TESTNET_GAS_STATION_ID = 156575978
TESTNET_FACTORY_CONSTANT_PRODUCT_ID = 164584393

Network = Literal["mainnet", "testnet", "dev"]


@dataclasses.dataclass
class Config:
    api_url: str = ""
    gas_station_id: int = 0
    factory_constant_product_id: int = 0
    factory_constant_product_fee_bps: list[int] = dataclasses.field(
        default_factory=lambda: list(CONSTANT_PRODUCT_FEE_BPS)
    )


def get_config(network: Network, **kwargs) -> Config:
    if network == "mainnet":
        params: dict = {
            "api_url": MAINNET_API_URL,
            "gas_station_id": MAINNET_GAS_STATION_ID,
            "factory_constant_product_id": MAINNET_FACTORY_CONSTANT_PRODUCT_ID,
            **kwargs,
        }
    elif network == "testnet":
        params = {
            "api_url": TESTNET_API_URL,
            "gas_station_id": TESTNET_GAS_STATION_ID,
            "factory_constant_product_id": TESTNET_FACTORY_CONSTANT_PRODUCT_ID,
            **kwargs,
        }
    elif network == "dev":
        params = {
            "api_url": "",
            "gas_station_id": 0,
            "factory_constant_product_id": 0,
            **kwargs,
        }
    else:
        raise ValueError(f"No predefined config for network {network}")

    return Config(**params)
