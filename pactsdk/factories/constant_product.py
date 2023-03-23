import dataclasses

import algosdk

from ..transaction_group import TransactionGroup
from ..utils import get_selector, sp_fee
from .base_factory import (
    PoolBuildParams,
    PoolFactory,
    PoolParams,
    get_contract_deploy_cost,
)


def build_constant_product_tx_group(
    factory_id: int,
    sender: str,
    sp: algosdk.transaction.SuggestedParams,
    pool_params: PoolParams,
) -> TransactionGroup:

    deployment_cost = get_contract_deploy_cost(
        is_algo=pool_params.primary_asset_id == 0,
        extra_pages=1,
        num_byte_slices=2,
        num_uint=0,
    )

    fund_tx = algosdk.transaction.PaymentTxn(
        sender=sender,
        receiver=algosdk.logic.get_application_address(factory_id),
        amt=deployment_cost,
        sp=sp,
    )

    app_args: list = [
        get_selector("build(asset,asset,uint64)uint64"),
        algosdk.abi.UintType(8).encode(0),
        algosdk.abi.UintType(8).encode(1),
        algosdk.abi.UintType(64).encode(pool_params.fee_bps),
    ]

    box_name = pool_params.to_box_name()

    build_tx = algosdk.transaction.ApplicationNoOpTxn(
        sender=sender,
        index=factory_id,
        app_args=app_args,
        sp=sp_fee(sp, 10000),
        boxes=[(0, box_name)],
        foreign_assets=[
            pool_params.primary_asset_id,
            pool_params.secondary_asset_id,
        ],
    )

    return TransactionGroup([fund_tx, build_tx])


@dataclasses.dataclass
class ConstantProductFactory(PoolFactory):
    def build_tx_group(
        self,
        sender: str,
        sp: algosdk.transaction.SuggestedParams,
        pool_build_params: PoolBuildParams,
    ):
        return build_constant_product_tx_group(
            factory_id=self.app_id,
            sender=sender,
            sp=sp,
            pool_params=PoolParams(
                **dataclasses.asdict(pool_build_params),
                version=self.state.pool_version,
            ),
        )
