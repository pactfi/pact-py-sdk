import base64
import dataclasses
from typing import Callable, Optional

import algosdk

from pactsdk.encoding import deserialize_uint64

from ..pool import Pool, fetch_pool_by_id
from ..transaction_group import TransactionGroup
from ..utils import get_box_min_balance, parse_app_state, wait_for_confirmation

Signer = Callable[[TransactionGroup], list[algosdk.transaction.SignedTransaction]]


def get_contract_deploy_cost(
    extra_pages: int, num_byte_slices: int, num_uint: int, is_algo: bool
):
    cost = 100_000 + 100_000 * extra_pages
    cost += num_byte_slices * 50_000
    cost += num_uint * 28_500
    cost += get_box_min_balance(32, 8)

    # exchange opt-ins & min balance
    cost += 300_000 if is_algo else 400_000

    return cost + 300000


@dataclasses.dataclass
class PoolParams:
    primary_asset_id: int
    secondary_asset_id: int
    fee_bps: int
    version: int

    abi = algosdk.abi.ArrayStaticType(algosdk.abi.UintType(64), 4)

    def __hash__(self):
        return hash(self.as_tuple())

    def as_tuple(self):
        return (
            self.primary_asset_id,
            self.secondary_asset_id,
            self.fee_bps,
            self.version,
        )

    def to_box_name(self) -> bytes:
        return self.abi.encode(self.as_tuple())

    @classmethod
    def from_box_name(cls, name: str):
        values = cls.abi.decode(base64.b64decode(name))
        return cls(*values)


@dataclasses.dataclass
class PoolBuildParams:
    primary_asset_id: int
    secondary_asset_id: int
    fee_bps: int


@dataclasses.dataclass
class FactoryState:
    pool_version: int
    allowed_fee_bps: list[int]


def parse_global_factory_state(raw_state: list) -> FactoryState:
    """
    Args:
        raw_state: The contract's global state retrieved from algosdk.
    """
    state = parse_app_state(raw_state)
    return FactoryState(
        pool_version=state["POOL_CONTRACT_VERSION"],
        allowed_fee_bps=deserialize_uint64(state["ALLOWED_FEE_BPS"]),
    )


def list_pools(
    algod: algosdk.v2client.algod.AlgodClient,
    factory_id: int,
) -> list[PoolParams]:
    boxes = algod.application_boxes(factory_id)
    return [PoolParams.from_box_name(box["name"]) for box in boxes["boxes"]]


def fetch_pool_id(
    algod: algosdk.v2client.algod.AlgodClient,
    factory_id: int,
    pool_params: PoolParams,
) -> int:
    box_name = pool_params.to_box_name()
    try:
        box = algod.application_box_by_name(factory_id, box_name)
    except algosdk.error.AlgodHTTPError as e:
        if "box not found" in str(e):
            return 0
        raise e
    return int.from_bytes(base64.b64decode(box["value"]), "big")


@dataclasses.dataclass
class PoolFactory:
    """Abstract class for pool factories.

    The pool factory allows decentralization of pools creation and discoverability.
    Each pool type has a separate factory contract that deploys the pool. Every pool created by the pool factory can be trusted as a valid Pact pool.

    The factory ensures pools uniqueness meaning you can't create two pools with the same parameters using a single factory contract.
    """

    algod: algosdk.v2client.algod.AlgodClient
    app_id: int
    state: FactoryState

    def list_pools(self) -> list[PoolParams]:
        """Lists all pools created by this factory. It works by reading the boxes created by this factory. The boxes serve as a hash map of unlimited size. The box name stores pool parameters and the box content stores pool id.

        This method returns only pool parameters without the application id. You have to call `fetch_pool` to fetch the actual pool e.g.

        pool_params = factory.list_pools()
        pool = factory.fetch_pool(pool_params[0])

        Returns:
            List of pool parameters.
        """
        return list_pools(self.algod, self.app_id)

    def fetch_pool_id(self, pool_params: PoolParams) -> int:
        return fetch_pool_id(self.algod, self.app_id, pool_params)

    def fetch_pool(self, pool_params: PoolParams) -> Optional[Pool]:
        """Fetches the pool for the given params.

        Args:
            pool_params: Parameters of the pool with are looking for.

        Returns:
            A pool if pool with given parameters exists, None otherwise.
        """
        pool_id = self.fetch_pool_id(pool_params)
        if pool_id == 0:
            return None
        return fetch_pool_by_id(self.algod, pool_id)

    def build(
        self, sender: str, pool_build_params: PoolBuildParams, signer: Signer
    ) -> Pool:
        """Deploys a new pool to the network.

        Args:
            sender: The address that is going to send the transactions.
            pool_build_params: Parameters of the pool that is going to be created.
            signer: A callback that allows signing the transaction.

        Returns:
            The created pool instance.
        """
        assert (
            pool_build_params.fee_bps in self.state.allowed_fee_bps
        ), f"only one of {self.state.allowed_fee_bps} is allowed for fee_bps"

        sp = self.algod.suggested_params()
        tx_group = self.build_tx_group(
            sender=sender,
            pool_build_params=pool_build_params,
            sp=sp,
        )
        signed_txs = signer(tx_group)
        self.algod.send_transactions(signed_txs)
        txid = tx_group.transactions[-1].get_txid()
        wait_for_confirmation(self.algod, txid)
        txinfo = self.algod.pending_transaction_info(txid)
        pool_id = txinfo["inner-txns"][0]["application-index"]
        return fetch_pool_by_id(self.algod, pool_id)

    def build_or_get(
        self, sender: str, pool_build_params: PoolBuildParams, signer: Signer
    ) -> tuple[Pool, bool]:
        """Deploys a new pool to the network if the pool with the specified params does not exist yet. Otherwise, it returns the existing pool.

        Args:
            sender: The address that is going to send the transactions.
            pool_build_params: Parameters of the pool that is going to be created.
            signer: A callback that allows signing the transaction.

        Returns:
            The two items tuple. The first item is the created or existing pool. The second item is True if a new pool is created or False if an existing pool is returned.
        """

        try:
            new_pool = self.build(sender, pool_build_params, signer)
            return new_pool, True
        except algosdk.error.AlgodHTTPError as e:
            existing_pool = self.fetch_pool(
                PoolParams(
                    **dataclasses.asdict(pool_build_params),
                    version=self.state.pool_version,
                )
            )
            if existing_pool:
                return existing_pool, False
            raise e

    def build_tx_group(
        self,
        sender: str,
        sp: algosdk.transaction.SuggestedParams,
        pool_build_params: PoolBuildParams,
    ):
        raise NotImplementedError
