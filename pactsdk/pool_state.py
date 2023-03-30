from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Optional

from pactsdk.encoding import (
    decode_address_from_global_state,
    decode_string_from_global_state,
    deserialize_uint64,
)

from .utils import parse_app_state

if TYPE_CHECKING:
    from pactsdk.pool import PoolType


@dataclass
class AppInternalState:
    """The one to one representation of pool's global state."""

    # Properties shared for all contracts.
    A: int
    B: int
    ASSET_A: int
    ASSET_B: int
    LTID: int
    L: int
    FEE_BPS: int

    # Those may be missing in older contracts.
    CONTRACT_NAME: Optional[Literal["PACT AMM", "[SI] PACT AMM"]] = None
    VERSION: Optional[int] = None
    PACT_FEE_BPS: Optional[int] = None
    ADMIN: Optional[str] = None
    FUTURE_ADMIN: Optional[str] = None
    TREASURY: Optional[str] = None
    PRIMARY_FEES: Optional[int] = None
    SECONDARY_FEES: Optional[int] = None

    # Stableswaps only below.
    INITIAL_A: Optional[int] = None
    INITIAL_A_TIME: Optional[int] = None
    FUTURE_A: Optional[int] = None
    FUTURE_A_TIME: Optional[int] = None
    PRECISION: Optional[int] = None


@dataclass
class PoolState:
    """A user friendly representation of pool's global state."""

    total_liquidity: int
    total_primary: int
    total_secondary: int
    primary_asset_price: float
    secondary_asset_price: float


def parse_global_pool_state(raw_state: list) -> AppInternalState:
    """
    Args:
        raw_state: The contract's global state retrieved from algosdk.
    """
    state = parse_app_state(raw_state)

    if "CONTRACT_NAME" in state:
        state["CONTRACT_NAME"] = decode_string_from_global_state(state["CONTRACT_NAME"])

    if "ADMIN" in state:
        state["ADMIN"] = decode_address_from_global_state(state["ADMIN"])

    if "TREASURY" in state:
        state["TREASURY"] = decode_address_from_global_state(state["TREASURY"])

    if "INITIAL_A" in state:
        asset_a, asset_b, _, precision = deserialize_uint64(state.pop("CONFIG"))

        return AppInternalState(
            ASSET_A=asset_a,
            ASSET_B=asset_b,
            PRECISION=precision,
            **state,
        )

    if "FEE_BPS" in state:
        del state["FEE_BPS"]

    asset_a, asset_b, fee_bps = deserialize_uint64(state.pop("CONFIG"))
    return AppInternalState(ASSET_A=asset_a, ASSET_B=asset_b, FEE_BPS=fee_bps, **state)


def get_pool_type_from_internal_state(
    state: AppInternalState,
) -> "PoolType":
    if state.CONTRACT_NAME == "PACT AMM":
        return "CONSTANT_PRODUCT"

    if state.CONTRACT_NAME == "PACT AMM [NFT]":
        return "NFT_CONSTANT_PRODUCT"

    if state.CONTRACT_NAME == "[SI] PACT AMM":
        return "STABLESWAP"

    # Older contracts are missing CONTRACT_NAME. Let's assume it's our good old constant product.
    return "CONSTANT_PRODUCT"
