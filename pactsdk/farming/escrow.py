"""
This module contains utilities for interacting with the escrow contract.
Each user deploys his own application which holds staked assets for only this user and for only one farm.
The contract is very minimal and has strong guarantees for user funds safety.
"""

import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import algosdk
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

from ..gas_station import get_gas_station
from ..utils import get_selector, parse_app_state, sp_fee

if TYPE_CHECKING:
    from .farm import Farm

COMPILED_APPROVAL_PROGRAM_B64 = "CCADAAYBJgMLTWFzdGVyQXBwSUQBAQEAMgkxABJEMRlAAIoxGEAAQzYaAIAEOIgacRJEKDYaARfAMmexI7IQNhoCF8AyshiABLc1X9GyGiKyAbOxgQSyEDIKshQ2GgMXwDCyESKyAbNCAF42GgCABA2GHEISRLEjshAoZLIYgATDFArnshopshoqshopshoqshoyCbIcMgiyMjYaAhfAMLIwMgmyICKyAbNCABwxGYEFEkAAAQAyCShkYRREsSSyECKyATIJsiCzJEM="
COMPILED_CLEAR_PROGRAM_B64 = "CIEBQw=="

REKEY_TO_USER_FEE = 2000
REKEY_TO_CONTRACT_FEE = 1000

CREATE_SIG = get_selector("create(application,application,asset)void")
REKEY_TO_CREATOR_SIG = get_selector("rekey_to_creator(application,asset)void")


@dataclass
class EscrowInternalState:
    master_app: int


def build_deploy_escrow_txs(
    sender: str,
    farm_app_id: int,
    staked_asset_id: int,
    suggested_params: transaction.SuggestedParams,
) -> list[transaction.Transaction]:

    approval_program = base64.b64decode(COMPILED_APPROVAL_PROGRAM_B64)
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
        sp=sp_fee(suggested_params, 4000),
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


def list_escrows_from_account_info(
    algod: AlgodClient,
    account_info: dict,
    farms: Optional[list["Farm"]] = None,
) -> list["Escrow"]:
    from .farm import fetch_farm_by_id

    farms_by_id = {farm.app_id: farm for farm in farms or []}
    escrows: list[Escrow] = []

    for app_info in account_info["created-apps"]:
        if app_info["params"]["approval-program"] != COMPILED_APPROVAL_PROGRAM_B64:
            continue

        state = parse_global_escrow_state(app_info["params"]["global-state"])
        creator = app_info["params"]["creator"]

        if farms is None:
            farm = fetch_farm_by_id(algod, state.master_app)
        else:
            farm = farms_by_id.get(state.master_app)

        if farm is None:
            continue

        escrows.append(
            Escrow(
                algod=algod,
                app_id=app_info["id"],
                user_address=creator,
                farm=farm,
                state=state,
            )
        )

    return escrows


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
    suggested_params: transaction.SuggestedParams = None
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

    def set_suggested_params(
        self, suggested_params: algosdk.future.transaction.SuggestedParams
    ):
        self.suggested_params = suggested_params

    def refresh_suggested_params(self):
        self.set_suggested_params(self.algod.suggested_params())

    def fetch_user_state(self):
        return self.farm.fetch_user_state(self.user_address)

    def get_user_state_from_account_info(self, account_info: dict):
        return self.farm.get_user_state_from_account_info(account_info)

    def build_rekey_to_user_tx(self, fee=REKEY_TO_USER_FEE) -> transaction.Transaction:
        return transaction.ApplicationNoOpTxn(
            sender=self.user_address,
            index=self.app_id,
            foreign_apps=[self.farm.app_id],
            foreign_assets=[self.farm.staked_asset.index],
            app_args=[REKEY_TO_CREATOR_SIG, 1, 0],
            sp=sp_fee(self.suggested_params, fee),
        )

    def build_rekey_to_contract_tx(
        self, fee=REKEY_TO_CONTRACT_FEE
    ) -> transaction.Transaction:
        return transaction.PaymentTxn(
            sender=self.address,
            receiver=self.address,
            amt=0,
            rekey_to=self.address,
            sp=sp_fee(self.suggested_params, fee),
        )

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
        with self.rekey() as txs:
            transfer_tx = self.farm.staked_asset.build_transfer_tx(
                sender=self.address,
                receiver=self.user_address,
                amount=amount,
                suggested_params=sp_fee(self.suggested_params, 0),
            )
            txs.append(transfer_tx)
        return txs

    def build_claim_rewards_tx(self) -> transaction.Transaction:
        return self.farm.build_claim_rewards_tx(self)

    def build_delete_tx(self) -> transaction.Transaction:
        return transaction.ApplicationDeleteTxn(
            sender=self.user_address,
            index=self.app_id,
            foreign_apps=[self.farm.app_id],
            sp=sp_fee(self.suggested_params, 2000),
        )

    def build_clear_txs(self) -> list[transaction.Transaction]:
        is_opted_in = self.farm.staked_asset.is_opted_in(self.address)

        txs: list[transaction.Transaction] = []

        # Claim staked tokens if needed.
        if is_opted_in:
            txs.append(
                self.farm.staked_asset.build_opt_out_tx(
                    address=self.address,
                    close_to=self.user_address,
                    suggested_params=self.suggested_params,
                )
            )

        txs.append(
            transaction.PaymentTxn(
                sender=self.address,
                receiver=self.user_address,
                amt=0,
                sp=self.suggested_params,
                close_remainder_to=self.user_address,
            )
        )

        return txs

    def build_delete_and_clear_txs(self) -> list[transaction.Transaction]:
        farm_opt_out = transaction.ApplicationCloseOutTxn(
            sender=self.user_address, sp=self.suggested_params, index=self.farm.app_id
        )
        delete_tx = self.build_delete_tx()
        clear_txs = self.build_clear_txs()

        return [farm_opt_out, delete_tx, *clear_txs]

    @contextmanager
    def rekey(self):
        """
        Example usage:

        with escrow.rekey() as txs:
            gov_tx = build_governance_commit_tx(escrow.address, 1000)
            txs.append(gov_tx)
        """

        fee = REKEY_TO_USER_FEE + REKEY_TO_CONTRACT_FEE + 2000

        txs: list[transaction.Transaction] = [
            self.farm.build_update_increase_opcode_quota_tx(self.user_address),
            self.build_rekey_to_user_tx(fee=fee),
        ]

        yield txs

        txs.append(self.build_rekey_to_contract_tx(fee=0))
        txs.append(self.farm.build_update_tx(self))
