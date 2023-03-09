import base64
import dataclasses
from typing import Any, Callable, Optional

import algosdk

from .config import Config
from .pool import Pool, PoolType, fetch_pool_by_id
from .transaction_group import TransactionGroup
from .utils import get_box_min_balance, get_selector, sp_fee, wait_for_confirmation

Signer = Callable[[TransactionGroup], list[algosdk.transaction.SignedTransaction]]


def get_contract_deploy_cost(
    extra_pages: int, num_byte_slices: int, num_uint: int, is_algo: bool
):
    cost = 100_000 + 100_000 * extra_pages
    cost += num_byte_slices * 50_000
    cost += num_uint * 28_500
    cost += get_box_min_balance(24, 8)

    # exchange opt-ins & min balance
    cost += 300_000 if is_algo else 400_000

    return cost + 300000


@dataclasses.dataclass
class ConstantProductParams:
    primary_asset_id: int
    secondary_asset_id: int
    fee_bps: int

    abi = algosdk.abi.ArrayStaticType(algosdk.abi.UintType(64), 3)

    def __hash__(self):
        return hash(self.as_tuple())

    def as_tuple(self):
        return self.primary_asset_id, self.secondary_asset_id, self.fee_bps

    def to_box_name(self) -> bytes:
        return self.abi.encode(self.as_tuple())

    @classmethod
    def from_box_name(cls, name: str) -> "ConstantProductParams":
        values = cls.abi.decode(base64.b64decode(name))
        return ConstantProductParams(*values)


def list_pools(
    algod: algosdk.v2client.algod.AlgodClient, factory_id: int
) -> list[ConstantProductParams]:
    boxes = algod.application_boxes(factory_id)
    return [ConstantProductParams.from_box_name(box["name"]) for box in boxes["boxes"]]


def get_pool_id(
    algod: algosdk.v2client.algod.AlgodClient,
    factory_id: int,
    pool_params: ConstantProductParams,
) -> int:
    box_name = pool_params.to_box_name()
    try:
        box = algod.application_box_by_name(factory_id, box_name)
    except algosdk.error.AlgodHTTPError as e:
        if "box not found" in str(e):
            return 0
        raise e
    return int.from_bytes(base64.b64decode(box["value"]), "big")


def build_constant_product_tx_group(
    factory_id: int,
    sender: str,
    sp: algosdk.transaction.SuggestedParams,
    pool_params: ConstantProductParams,
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
class PoolFactory:
    """Abstract class for pool factories.

    The pool factory allows decentralization of pools creation and discoverability.
    Each pool type has a separate factory contract that deploys the pool. Every pool created by the pool factory can be trusted as a valid Pact pool.

    The factory ensures pools uniqueness meaning you can't create two pools with the same parameters using a single factory contract.
    """

    algod: algosdk.v2client.algod.AlgodClient
    app_id: int
    config: Optional[Config] = None

    def list_pools(self) -> list[Any]:
        """Lists all pools created by this factory. It works by reading the boxes created by this factory. The boxes serve as a hash map of unlimited size. The box name stores pool parameters and the box content stores pool id.

        This method returns only pool parameters without the application id. You have to call `fetch_pool` to fetch the actual pool e.g.

        pool_params = factory.list_pools()
        pool = factory.fetch_pool(pool_params[0])

        Returns:
            List of pool parameters.
        """
        return list_pools(self.algod, self.app_id)

    def fetch_pool(self, pool_params: ConstantProductParams) -> Optional[Pool]:
        """Fetches the pool for the given params.

        Args:
            pool_params: Parameters of the pool with are looking for.

        Returns:
            A pool if pool with given parameters exists, None otherwise.
        """
        pool_id = get_pool_id(self.algod, self.app_id, pool_params)
        if pool_id == 0:
            return None
        return fetch_pool_by_id(self.algod, pool_id)

    def build(self, sender: str, pool_params: Any, signer: Signer) -> Pool:
        """Deploys a new pool to the network.

        Args:
            sender: The address that is going to send the transactions.
            pool_params: Parameters of the pool that is going to be created.
            signer: A callback that allows signing the transaction.

        Returns:
            The created pool instance.
        """
        sp = self.algod.suggested_params()
        tx_group = self.build_tx_group(
            sender=sender,
            pool_params=pool_params,
            sp=sp,
        )
        signed_txs = signer(tx_group)
        self.algod.send_transactions(signed_txs)
        txid = tx_group.transactions[-1].get_txid()
        wait_for_confirmation(self.algod, txid)
        txinfo = self.algod.pending_transaction_info(txid)
        pool_id = txinfo["inner-txns"][0]["application-index"]
        return fetch_pool_by_id(self.algod, pool_id)

    def build_tx_group(
        self,
        sender: str,
        sp: algosdk.transaction.SuggestedParams,
        pool_params: Any,
    ):
        raise NotImplementedError


class ConstantProductFactory(PoolFactory):
    def build_tx_group(
        self,
        sender: str,
        sp: algosdk.transaction.SuggestedParams,
        pool_params: ConstantProductParams,
    ):
        if self.config:
            assert (
                pool_params.fee_bps in self.config.factory_constant_product_fee_bps
            ), f"only one of {self.config.factory_constant_product_fee_bps} is allowed for fee_bps"

        return build_constant_product_tx_group(
            factory_id=self.app_id,
            sender=sender,
            sp=sp,
            pool_params=pool_params,
        )


def get_pool_factory(
    algod: algosdk.v2client.algod.AlgodClient, pool_type: PoolType, config: Config
) -> PoolFactory:
    if pool_type == "CONSTANT_PRODUCT":
        assert (
            config.factory_constant_product_id
        ), "factory_constant_product_id is missing in the config."
        return ConstantProductFactory(algod, config.factory_constant_product_id, config)

    raise NotImplementedError(f"Factory for {pool_type} is not implemented yet.")
