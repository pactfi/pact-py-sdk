import algosdk

from ..config import Config
from ..pool import PoolType
from .base_factory import PoolFactory, parse_global_factory_state
from .constant_product import ConstantProductFactory


def get_pool_factory(
    algod: algosdk.v2client.algod.AlgodClient, pool_type: PoolType, config: Config
) -> PoolFactory:
    if pool_type == "CONSTANT_PRODUCT":
        app_id = config.factory_constant_product_id
        factory_class = ConstantProductFactory
    elif pool_type == "NFT_CONSTANT_PRODUCT":
        app_id = config.factory_nft_constant_product_id
        factory_class = ConstantProductFactory
    else:
        raise NotImplementedError(f"Factory for {pool_type} is not implemented yet.")

    assert app_id, f"Missing factory id for {pool_type} factory"
    app_info = algod.application_info(app_id)
    factory_state = parse_global_factory_state(app_info["params"]["global-state"])
    return factory_class(
        algod=algod,
        app_id=app_id,
        state=factory_state,
    )
