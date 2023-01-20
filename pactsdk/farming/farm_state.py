import datetime
from dataclasses import dataclass
from typing import TypeVar, Union

from algosdk.v2client.algod import AlgodClient

from pactsdk.asset import Asset

from ..asset import get_cached_asset
from ..encoding import decode_address_from_global_state, deserialize_uint64

T = TypeVar("T", bound=Union[int, float])

FarmingRewards = dict[Asset, T]


@dataclass()
class FarmInternalState:
    staked_asset_id: int
    reward_asset_ids: list[int]
    distributed_rewards: list[int]
    claimed_rewards: list[int]
    pending_rewards: list[int]
    next_rewards: list[int]
    rpt_frac: list[int]
    rpt: list[int]
    duration: int
    next_duration: int
    num_stakers: int
    total_staked: int
    updated_at: int
    admin: str
    updater: str
    version: int


@dataclass()
class FarmState:
    staked_asset: Asset
    """The asset the users are going to stake in the farm."""

    reward_assets: list[Asset]
    """Assets that are distributed as rewards in the farm."""

    distributed_rewards: FarmingRewards[int]
    """Amounts of assets distributed so far. This includes tokens that are already claimed and tokens which are accrued and are awaiting claim."""

    claimed_rewards: FarmingRewards[int]
    """Amounts of assets claimed by users so far."""

    pending_rewards: FarmingRewards[int]
    """Amounts of not yet distributed rewards in the farm."""

    rpt: FarmingRewards[float]
    """Current rate per token for each asset."""

    duration: int
    """Time in seconds until current cycle ends. This is the time at which the rewards are depleted. Next cycle is automatically picked up if next_rewards are deposited."""

    next_duration: int
    """The duration of the next cycle."""

    next_rewards: FarmingRewards[int]
    """Amounts of rewards deposited for the next cycle."""

    num_stakers: int
    """The number of active stakers. Active staker stakes at least 1 token."""

    total_staked: int
    """The sum of all stakers deposits."""

    updated_at: datetime.datetime
    """The time the farm was last updated."""

    admin: str
    """The address of the farm's admin account. The admin can deposit new rewards and destroy the farm after it is deprecated."""

    updater: str
    """The address of farm's updater. The updater can update the farm's contract to a new version."""

    version: int
    """Contract version."""

    @property
    def rewards_per_second(self) -> FarmingRewards[float]:
        return {
            asset: amount / self.duration
            for asset, amount in self.pending_rewards.items()
        }


@dataclass
class FarmUserState:
    escrow_id: int
    """The app id of the user's escrow contract."""

    staked: int
    """The amount of staked asset the user has deposited in the escrow."""

    accrued_rewards: FarmingRewards[int]
    """Amounts of rewards the user has accrued and can claim."""

    claimed_rewards: FarmingRewards[int]
    """Amounts of rewards the user has already claimed."""

    rpt: FarmingRewards[float]
    """Current rate per token for each asset."""


def parse_internal_state(raw_state: dict) -> FarmInternalState:
    return FarmInternalState(
        claimed_rewards=deserialize_uint64(raw_state["ClaimedRewards"]),
        duration=raw_state["Duration"],
        next_duration=raw_state["NextDuration"],
        next_rewards=deserialize_uint64(raw_state["NextRewards"]),
        num_stakers=raw_state["NumStakers"],
        pending_rewards=deserialize_uint64(raw_state["PendingRewards"]),
        rpt=deserialize_uint64(raw_state["RPT"]),
        rpt_frac=deserialize_uint64(raw_state["RPT_frac"]),
        reward_asset_ids=deserialize_uint64(raw_state["RewardAssetIDs"]),
        staked_asset_id=raw_state["StakedAssetID"],
        distributed_rewards=deserialize_uint64(raw_state["TotalRewards"]),
        total_staked=raw_state["TotalStaked"],
        updated_at=raw_state["UpdatedAt"],
        admin=decode_address_from_global_state(raw_state["Admin"]),
        updater=decode_address_from_global_state(raw_state["Updater"]),
        version=raw_state["VERSION"],
    )


def internal_state_to_state(
    algod: AlgodClient, internal_state: FarmInternalState
) -> FarmState:
    staked_asset = get_cached_asset(
        algod=algod, index=internal_state.staked_asset_id, decimals=0
    )

    reward_assets = [
        get_cached_asset(algod=algod, index=asset_id, decimals=0)
        for asset_id in internal_state.reward_asset_ids
    ]

    rpt = format_rpt(internal_state.rpt, internal_state.rpt_frac)

    return FarmState(
        staked_asset=staked_asset,
        reward_assets=reward_assets,
        distributed_rewards=format_rewards(
            reward_assets, internal_state.distributed_rewards
        ),
        claimed_rewards=format_rewards(reward_assets, internal_state.claimed_rewards),
        pending_rewards=format_rewards(reward_assets, internal_state.pending_rewards),
        next_rewards=format_rewards(reward_assets, internal_state.next_rewards),
        rpt=format_rewards(reward_assets, rpt),
        duration=internal_state.duration,
        next_duration=internal_state.next_duration,
        num_stakers=internal_state.num_stakers,
        total_staked=internal_state.total_staked,
        updated_at=datetime.datetime.fromtimestamp(internal_state.updated_at),
        admin=internal_state.admin,
        updater=internal_state.updater,
        version=internal_state.version,
    )


def format_rewards(assets: list[Asset], amounts: list[T]) -> FarmingRewards[T]:
    return {asset: amount for asset, amount in zip(assets, amounts)}


def format_rpt(rpt_whole: list[int], rpt_frac: list[int]) -> list[float]:
    assert len(rpt_whole) == len(rpt_frac)
    return [whole + frac / 2**64 for whole, frac in zip(rpt_whole, rpt_frac)]
