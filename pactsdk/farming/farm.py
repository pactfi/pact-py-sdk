"""
This module container utilities for interacting with the farm contract.
"""

import datetime
from dataclasses import dataclass, field
from typing import Optional

import algosdk
from algosdk import abi, transaction
from algosdk.v2client.algod import AlgodClient

from pactsdk.asset import Asset, fetch_asset_by_index

from ..encoding import deserialize_uint64
from ..gas_station import get_gas_station
from ..utils import get_selector, parse_app_state, sp_fee
from .escrow import Escrow, build_deploy_escrow_txs, fetch_escrow_by_id
from .farm_state import (
    FarmingRewards,
    FarmInternalState,
    FarmState,
    FarmUserState,
    format_rewards,
    format_rpt,
    internal_state_to_state,
    parse_internal_state,
)

UPDATE_TX_FEE = 3000
MAX_REWARD_ASSETS = 7

UPDATE_GLOBAL_STATE_SIG = get_selector("update_global_state()void")
UPDATE_STATE_SIG = get_selector("update_state(application,account,account,asset)void")
CLAIM_REWARDS_SIG = get_selector("claim_rewards(account,uint64[])void")
ADD_REWARD_ASSET_SIG = get_selector("add_reward_asset(asset)void")
DEPOSIT_REWARDS_SIG = get_selector("deposit_rewards(uint64[],uint64)void")


def fetch_farm_raw_state_by_id(algod: AlgodClient, app_id: int) -> dict:
    app_info = algod.application_info(app_id)
    return parse_app_state(app_info["params"]["global-state"])


def make_farm_from_raw_state(
    algod: AlgodClient, app_id: int, raw_state: dict
) -> "Farm":
    internal_state = parse_internal_state(raw_state)
    state = internal_state_to_state(algod, internal_state)

    return Farm(
        algod=algod,
        app_id=app_id,
        raw_state=raw_state,
        internal_state=internal_state,
        state=state,
    )


def fetch_farm_by_id(algod: AlgodClient, app_id: int):
    raw_state = fetch_farm_raw_state_by_id(algod, app_id)
    return make_farm_from_raw_state(algod, app_id, raw_state)


@dataclass
class Farm:
    algod: AlgodClient
    """The Algorand client to use."""

    app_id: int
    """The application id for the farming."""

    raw_state: dict

    internal_state: FarmInternalState

    state: FarmState

    _suggested_params: Optional[algosdk.transaction.SuggestedParams] = None

    app_address: str = field(init=False)

    def __post_init__(self):
        self.app_address = algosdk.logic.get_application_address(self.app_id)

    def __hash__(self):
        return self.app_id

    def __str__(self):
        return f"Farm {self.staked_asset} ({self.app_id})"

    def __eq__(self, other_obj: object) -> bool:
        if not isinstance(other_obj, Farm):
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

    def fetch_all_assets(self):
        self.state.staked_asset = fetch_asset_by_index(
            self.algod, self.state.staked_asset.index
        )
        self.state.reward_assets = [
            fetch_asset_by_index(self.algod, asset.index)
            for asset in self.state.reward_assets
        ]

    @property
    def staked_asset(self):
        return self.state.staked_asset

    def have_rewards(self, dt: Optional[datetime.datetime] = None) -> bool:
        state = self.state

        if state.duration == 0:
            # Finished distributing rewards or there never were any rewards.
            return False

        if state.total_staked == 0:
            # The farm is paused and still has rewards.
            return True

        if dt is None:
            dt = datetime.datetime.now()

        duration = datetime.timedelta(seconds=state.duration + state.next_duration)
        if dt < state.updated_at + duration:
            # The farm is going and still has rewards.
            return True

        # All the rewards will be distributed at the specified time.
        return False

    def fetch_escrow_by_id(self, app_id: int) -> Escrow:
        return fetch_escrow_by_id(self.algod, app_id, farm=self)

    def fetch_escrow_by_address(self, address: str) -> Optional[Escrow]:
        user_state = self.fetch_user_state(address)
        if user_state is None:
            return None
        return fetch_escrow_by_id(self.algod, user_state.escrow_id, farm=self)

    def fetch_escrow_from_account_info(self, account_info: dict) -> Optional[Escrow]:
        user_state = self.get_user_state_from_account_info(account_info)
        if user_state is None:
            return None
        return fetch_escrow_by_id(self.algod, user_state.escrow_id, farm=self)

    def update_state(self):
        app_info = self.algod.application_info(self.app_id)
        self.raw_state = parse_app_state(app_info["params"]["global-state"])
        self.internal_state = parse_internal_state(self.raw_state)
        self.state = internal_state_to_state(self.algod, self.internal_state)

    def fetch_user_state(self, address: str) -> Optional[FarmUserState]:
        account_info = self.algod.account_info(address)
        return self.get_user_state_from_account_info(account_info)

    def get_user_state_from_account_info(
        self, account_info: dict
    ) -> Optional[FarmUserState]:
        try:
            raw_state = parse_app_state(
                next(
                    state["key-value"]
                    for state in account_info["apps-local-state"]
                    if state["id"] == self.app_id
                )
            )
        except StopIteration:
            return None

        rpt = format_rpt(
            deserialize_uint64(raw_state["RPT"]),
            deserialize_uint64(raw_state["RPT_frac"]),
        )

        return FarmUserState(
            escrow_id=raw_state["EscrowID"],
            staked=raw_state["Staked"],
            accrued_rewards=format_rewards(
                self.state.reward_assets,
                deserialize_uint64(raw_state["AccruedRewards"]),
            ),
            claimed_rewards=format_rewards(
                self.state.reward_assets,
                deserialize_uint64(raw_state["ClaimedRewards"]),
            ),
            rpt=format_rewards(self.state.reward_assets, rpt),
        )

    def estimate_accrued_rewards(
        self,
        at_time: datetime.datetime,
        user_state: FarmUserState,
    ) -> FarmingRewards[int]:
        past_accrued_rewards = self._calculate_past_accrued_rewards(
            staked_amount=user_state.staked, user_rpt=user_state.rpt
        )

        estimated_rewards = self.simulate_accrued_rewards(
            at_time=at_time,
            staked_amount=user_state.staked,
            total_staked=self.state.total_staked,
        )

        rewards = self._sum_rewards(estimated_rewards, user_state.accrued_rewards)
        return self._sum_rewards(rewards, past_accrued_rewards)

    def simulate_new_staker(
        self, at_time: datetime.datetime, staked_amount: int
    ) -> FarmingRewards[int]:
        return self.simulate_accrued_rewards(
            at_time=at_time,
            staked_amount=staked_amount,
            total_staked=self.state.total_staked + staked_amount,
            extrapolate_future_rewards=True,
        )

    def simulate_accrued_rewards(
        self,
        at_time: datetime.datetime,
        staked_amount: int,
        total_staked: int,
        extrapolate_future_rewards=False,
    ) -> FarmingRewards[int]:
        duration = int((at_time - self.state.updated_at).total_seconds())

        if total_staked == 0:
            return {asset: 0 for asset in self.state.reward_assets}

        stake_ratio = staked_amount / total_staked

        # Simulate pending rewards.
        rewards = self._simulate_cycle_rewards(
            stake_ratio=stake_ratio,
            rewards=self.state.pending_rewards,
            stake_duration=duration,
            cycle_duration=self.state.duration,
        )

        duration -= self.state.duration
        if duration <= 0:
            return rewards

        if self.state.next_duration:
            # Simulate next rewards if needed.
            rewards_b = self._simulate_cycle_rewards(
                stake_ratio=stake_ratio,
                rewards=self.state.next_rewards,
                stake_duration=duration,
                cycle_duration=self.state.next_duration,
            )
            rewards = self._sum_rewards(rewards, rewards_b)

            duration -= self.state.next_duration
            if duration <= 0:
                return rewards

        if not extrapolate_future_rewards:
            return rewards

        next_duration = self.state.next_duration or self.state.duration
        if next_duration == 0:
            return rewards

        next_rewards = (
            self.state.next_rewards
            if self.state.next_duration
            else self.state.pending_rewards
        )
        next_next_rewards = {
            asset: int(amount * (duration / next_duration))
            for asset, amount in next_rewards.items()
        }

        # Extrapolate rewards for the future.
        rewards_c = self._simulate_cycle_rewards(
            stake_ratio=stake_ratio,
            rewards=next_next_rewards,
            stake_duration=duration,
            cycle_duration=duration,
        )

        return self._sum_rewards(rewards, rewards_c)

    def _simulate_cycle_rewards(
        self,
        stake_ratio: float,
        rewards: FarmingRewards[int],
        stake_duration: int,
        cycle_duration: int,
    ) -> FarmingRewards[int]:
        if cycle_duration == 0:
            return {asset: 0 for asset in self.state.reward_assets}

        stake_duration = min(stake_duration, cycle_duration)

        return {
            asset: int(
                stake_ratio * rewards.get(asset, 0) * (stake_duration / cycle_duration)
            )
            for asset in self.state.reward_assets
        }

    def _calculate_past_accrued_rewards(
        self,
        staked_amount: int,
        user_rpt: FarmingRewards[float],
    ) -> FarmingRewards[int]:
        return {
            asset: int(
                (
                    max(0, self.state.rpt.get(asset, 0) - user_rpt.get(asset, 0))
                    * staked_amount
                )
            )
            for asset in self.state.reward_assets
        }

    def _sum_rewards(
        self, rewards_a: FarmingRewards[int], rewards_b: FarmingRewards[int]
    ) -> FarmingRewards[int]:
        return {
            asset: amount + rewards_b.get(asset, 0)
            for asset, amount in rewards_a.items()
        }

    def prepare_deploy_escrow_txs(self, sender: str) -> list[transaction.Transaction]:
        return build_deploy_escrow_txs(
            sender=sender,
            farm_app_id=self.app_id,
            staked_asset_id=self.staked_asset.index,
            suggested_params=self.suggested_params,
        )

    def build_update_increase_opcode_quota_tx(
        self, sender: str
    ) -> Optional[transaction.Transaction]:
        seconds_passed = (datetime.datetime.now() - self.state.updated_at).seconds
        opcodes_cost = 671 if seconds_passed > self.state.duration > 0 else 513
        count = (opcodes_cost * len(self.state.reward_assets)) // 700
        if count == 0:
            return None

        return get_gas_station().build_increase_opcode_quota_tx(
            sender=sender,
            count=count,
            suggested_params=self.suggested_params,
        )

    def build_update_with_opcode_increase_txs(
        self, escrow: Escrow
    ) -> list[transaction.Transaction]:
        txs = [self.build_update_tx(escrow)]

        if increase_opcode_quota_tx := self.build_update_increase_opcode_quota_tx(
            escrow.user_address
        ):
            txs.insert(0, increase_opcode_quota_tx)

        return txs

    def build_update_tx(self, escrow: Escrow) -> transaction.Transaction:
        return transaction.ApplicationNoOpTxn(
            sender=escrow.user_address,
            index=self.app_id,
            foreign_assets=[self.staked_asset.index],
            foreign_apps=[escrow.app_id],
            accounts=[escrow.address],
            app_args=[
                UPDATE_STATE_SIG,
                abi.UintType(8).encode(1),
                abi.UintType(8).encode(1),
                abi.UintType(8).encode(0),
                abi.UintType(8).encode(0),
            ],
            sp=sp_fee(self.suggested_params, UPDATE_TX_FEE),
        )

    def build_claim_rewards_tx(
        self, escrow: Escrow, assets: Optional[list[Asset]] = None
    ) -> transaction.Transaction:
        if assets is None:
            assets = self.state.reward_assets

        number_of_assets = len(assets)
        return transaction.ApplicationNoOpTxn(
            sender=escrow.user_address,
            index=self.app_id,
            foreign_assets=[asset.index for asset in assets],
            foreign_apps=[escrow.app_id],
            accounts=[escrow.user_address],
            app_args=[
                CLAIM_REWARDS_SIG,
                abi.UintType(8).encode(0),
                abi.ArrayDynamicType(abi.UintType(64)).encode(
                    [self.state.reward_assets.index(asset) for asset in assets]
                ),
            ],
            sp=sp_fee(self.suggested_params, 1000 * (number_of_assets + 1)),
        )

    def build_update_global_state_tx(self, sender: str):
        return transaction.ApplicationNoOpTxn(
            sender=sender,
            index=self.app_id,
            app_args=[UPDATE_GLOBAL_STATE_SIG],
            sp=self.suggested_params,
        )

    def admin_build_add_reward_asset_tx(self, asset: Asset) -> transaction.Transaction:
        return transaction.ApplicationNoOpTxn(
            sender=self.state.admin,
            sp=sp_fee(self.suggested_params, 2000),
            index=self.app_id,
            foreign_assets=[asset.index],
            app_args=[ADD_REWARD_ASSET_SIG, 0],
        )

    def admin_build_deposit_rewards_txs(
        self, rewards: FarmingRewards[int], duration: int
    ) -> list[transaction.Transaction]:
        assets_to_opt_in = [
            asset for asset in rewards.keys() if asset not in self.state.reward_assets
        ]

        assert (
            self.state.next_duration == 0
        ), "Cannot deposit next rewards if farm already have next rewards"

        assert (
            len(self.state.reward_assets) + len(assets_to_opt_in) <= MAX_REWARD_ASSETS
        ), f"Maximum number of reward assets per farm is {MAX_REWARD_ASSETS}"

        increase_opcode_tx = None
        if self.state.total_staked:
            increase_opcode_tx = self.build_update_increase_opcode_quota_tx(
                self.state.admin
            )

        update_tx = self.build_update_global_state_tx(sender=self.state.admin)

        # Fund farm with minimal ALGO balance required for assets opt-ins.
        opt_in_txs: list[transaction.Transaction] = [
            transaction.PaymentTxn(
                sender=self.state.admin,
                receiver=self.app_address,
                amt=len(assets_to_opt_in) * 100_000,
                sp=self.suggested_params,
            )
        ]

        if assets_to_opt_in:
            opt_in_txs += [
                self.admin_build_add_reward_asset_tx(asset)
                for asset in assets_to_opt_in
            ]

        for asset in assets_to_opt_in:
            self.state.reward_assets.append(asset)

        transfer_txs = [
            asset.build_transfer_tx(
                sender=self.state.admin,
                receiver=self.app_address,
                amount=amount,
                suggested_params=self.suggested_params,
            )
            for asset, amount in rewards.items()
        ]

        foreign_assets = [asset for asset in rewards.keys()]

        app_args = [
            DEPOSIT_REWARDS_SIG,
            abi.ArrayDynamicType(abi.UintType(64)).encode(
                [self.state.reward_assets.index(asset) for asset in foreign_assets]
            ),
            abi.UintType(64).encode(duration),
        ]

        deposit_rewards_tx = transaction.ApplicationNoOpTxn(
            sender=self.state.admin,
            sp=self.suggested_params,
            index=self.app_id,
            app_args=app_args,
        )

        txs = [
            increase_opcode_tx,
            update_tx,
            *opt_in_txs,
            *transfer_txs,
            deposit_rewards_tx,
        ]

        return [tx for tx in txs if tx]
