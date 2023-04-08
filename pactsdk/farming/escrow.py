"""
This module contains utilities for interacting with the escrow contract.
Each user deploys his own application which holds staked assets for only this user and for only one farm.
The contract is very minimal and has strong guarantees for user funds safety.
"""

import base64
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import algosdk
from algosdk import abi, transaction
from algosdk.v2client.algod import AlgodClient

from ..gas_station import get_gas_station
from ..utils import get_selector, parse_app_state, sp_fee

if TYPE_CHECKING:
    from .farm import Farm

COMPILED_HUSK_APPROVAL = "CCACAAExGEAASYALTWFzdGVyQXBwSUQ2GgEXwDJnsYEGshA2GgIXwDKyGIAEtzVf0bIaIrIBs7GBBLIQMgqyFCKyEjYaAxfAMLIRIrIBsyNCAAEjQw=="
COMPILED_CLEAR_PROGRAM_B64 = "CIEBQw=="

REKEY_TO_USER_FEE = 2000
REKEY_TO_CONTRACT_FEE = 1000

CREATE_SIG = get_selector("create(application,application,asset)void")
UNSTAKE_SIG = get_selector("unstake(asset,uint64,application)void")
SEND_MESSAGE_SIG = get_selector("send_message(account,string)void")
WITHDRAW_ALGOS_SIG = get_selector("withdraw_algos()void")


@dataclass
class EscrowInternalState:
    master_app: int


def fetch_escrow_approval_program(algod: AlgodClient, farm_app_id: int) -> bytes:
    box = algod.application_box_by_name(farm_app_id, b"Escrow")
    return base64.b64decode(box["value"])


def build_deploy_escrow_txs(
    sender: str,
    farm_app_id: int,
    staked_asset_id: int,
    suggested_params: transaction.SuggestedParams,
) -> list[transaction.Transaction]:

    approval_program = base64.b64decode(COMPILED_HUSK_APPROVAL)
    clear_program = base64.b64decode(COMPILED_CLEAR_PROGRAM_B64)

    gas_station = get_gas_station()

    fund_tx = gas_station.build_fund_tx(
        sender=sender,
        amount=200_000,
        suggested_params=suggested_params,
    )

    create_app_tx = transaction.ApplicationCreateTxn(
        sender=sender,
        approval_program=approval_program,
        clear_program=clear_program,
        on_complete=transaction.OnComplete.NoOpOC,
        global_schema=transaction.StateSchema(1, 0),
        local_schema=transaction.StateSchema(0, 0),
        sp=sp_fee(suggested_params, 5000),
        foreign_apps=[farm_app_id, gas_station.app_id],
        foreign_assets=[staked_asset_id],
        app_args=[CREATE_SIG, 1, 2, 0],
    )

    app_opt_in_tx = transaction.ApplicationOptInTxn(
        sender=sender, sp=suggested_params, index=farm_app_id
    )

    return [fund_tx, create_app_tx, app_opt_in_tx]


def fetch_escrow_by_id(
    algod: AlgodClient, app_id: int, farm: Optional["Farm"] = None
) -> "Escrow":
    state, creator = fetch_escrow_global_state(algod, app_id)
    if farm is None:
        from .farm import fetch_farm_by_id

        farm = fetch_farm_by_id(algod, state.master_app)

    assert (
        farm.app_id == state.master_app
    ), f'Escrow "{app_id}" doesn\'t match farm "{farm.app_id}".'

    return Escrow(
        algod=algod, app_id=app_id, user_address=creator, farm=farm, state=state
    )


def fetch_escrow_global_state(
    algod: AlgodClient, app_id: int
) -> tuple[EscrowInternalState, str]:
    app_info = algod.application_info(app_id)
    internal_state = parse_global_escrow_state(app_info["params"]["global-state"])
    creator = app_info["params"]["creator"]
    return internal_state, creator


def parse_global_escrow_state(raw_state: list) -> EscrowInternalState:
    state = parse_app_state(raw_state)
    return EscrowInternalState(master_app=state["MasterAppID"])


@dataclass
class Escrow:
    algod: AlgodClient
    app_id: int
    farm: "Farm"
    user_address: str
    state: EscrowInternalState
    _suggested_params: Optional[algosdk.transaction.SuggestedParams] = None
    address: str = field(init=False)

    def __post_init__(self):
        self.address = algosdk.logic.get_application_address(self.app_id)

    def __hash__(self):
        return self.app_id

    def __str__(self):
        return f"Escrow {self.user_address[:8]}... ({self.app_id}) for {self.farm}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other_obj: object) -> bool:
        if not isinstance(other_obj, Escrow):
            return False
        return self.app_id == other_obj.app_id

    @property
    def suggested_params(self) -> algosdk.transaction.SuggestedParams:
        assert self._suggested_params is not None
        return self._suggested_params

    def set_suggested_params(
        self, suggested_params: algosdk.transaction.SuggestedParams
    ):
        self._suggested_params = suggested_params

    def refresh_suggested_params(self):
        self.set_suggested_params(self.algod.suggested_params())

    def fetch_user_state(self):
        return self.farm.fetch_user_state(self.user_address)

    def get_user_state_from_account_info(self, account_info: dict):
        return self.farm.get_user_state_from_account_info(account_info)

    def build_stake_txs(self, amount: int) -> list[transaction.Transaction]:
        transfer_tx = self.farm.staked_asset.build_transfer_tx(
            sender=self.user_address,
            receiver=self.address,
            amount=amount,
            suggested_params=self.suggested_params,
        )
        update_txs = self.farm.build_update_with_opcode_increase_txs(self)

        return [transfer_tx, *update_txs]

    def build_unstake_txs(self, amount: int) -> list[transaction.Transaction]:
        unstake_tx = transaction.ApplicationNoOpTxn(
            sender=self.user_address,
            index=self.app_id,
            foreign_apps=[self.farm.app_id],
            foreign_assets=[self.farm.staked_asset.index],
            app_args=[
                UNSTAKE_SIG,
                abi.UintType(8).encode(0),
                abi.UintType(64).encode(amount),
                abi.UintType(8).encode(1),
            ],
            sp=sp_fee(self.suggested_params, 3000),
        )

        txs: list[transaction.Transaction] = [unstake_tx]

        if increase_opcode_quota_tx := self.farm.build_update_increase_opcode_quota_tx(
            self.user_address
        ):
            txs.insert(0, increase_opcode_quota_tx)

        return txs

    def build_claim_rewards_tx(self) -> transaction.Transaction:
        return self.farm.build_claim_rewards_tx(self)

    def build_send_message_tx(
        self, address: str, message: str
    ) -> transaction.Transaction:
        encoded_message = message.encode()
        note = algosdk.abi.UintType(16).encode(len(encoded_message)) + encoded_message
        return transaction.ApplicationNoOpTxn(
            sender=self.user_address,
            index=self.app_id,
            app_args=[SEND_MESSAGE_SIG, 1, note],
            accounts=[address],
            sp=sp_fee(self.suggested_params, 2000),
        )

    def build_withdraw_algos(self) -> transaction.Transaction:
        return transaction.ApplicationNoOpTxn(
            sender=self.user_address,
            index=self.app_id,
            app_args=[WITHDRAW_ALGOS_SIG],
            sp=sp_fee(self.suggested_params, 2000),
        )

    def build_force_exit_tx(self) -> transaction.Transaction:
        return transaction.ApplicationClearStateTxn(
            sender=self.user_address,
            index=self.farm.app_id,
            sp=self.suggested_params,
        )

    def build_exit_tx(self) -> transaction.Transaction:
        return transaction.ApplicationCloseOutTxn(
            sender=self.user_address,
            index=self.farm.app_id,
            sp=self.suggested_params,
        )

    def build_delete_tx(self) -> transaction.Transaction:
        return transaction.ApplicationDeleteTxn(
            sender=self.user_address,
            index=self.app_id,
            foreign_apps=[self.farm.app_id],
            foreign_assets=[self.farm.staked_asset.index],
            sp=sp_fee(self.suggested_params, 3000),
        )
