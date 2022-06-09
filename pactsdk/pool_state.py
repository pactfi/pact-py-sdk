import base64
from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass
class AppInternalState:
    """The one to one representation of pool's global state.

    The optional properties are used only by stableswaps and should not be relevant to the users.
    """

    A: int
    B: int
    ASSET_A: int
    ASSET_B: int
    LTID: int
    L: int
    FEE_BPS: int

    # Stableswaps only below.
    PACT_FEE_BPS: Optional[int] = None
    INITIAL_A: Optional[int] = None
    INITIAL_A_TIME: Optional[int] = None
    FUTURE_A: Optional[int] = None
    FUTURE_A_TIME: Optional[int] = None
    ADMIN: Optional[str] = None
    FUTURE_ADMIN: Optional[str] = None
    ADMIN_TRANSFER_DEADLINE: Optional[int] = None
    TREASURY: Optional[str] = None
    PRIMARY_FEES: Optional[int] = None
    SECONDARY_FEES: Optional[int] = None
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
    state = parse_state(raw_state)
    if "INITIAL_A" in state:
        asset_a, asset_b, fee_bps, precision = deserialize_uint64(state.pop("CONFIG"))
        return AppInternalState(
            ASSET_A=asset_a,
            ASSET_B=asset_b,
            FEE_BPS=fee_bps,
            PRECISION=precision,
            **state,
        )

    asset_a, asset_b, fee_bps = deserialize_uint64(state.pop("CONFIG"))
    return AppInternalState(ASSET_A=asset_a, ASSET_B=asset_b, FEE_BPS=fee_bps, **state)


def parse_state(kv: list) -> dict[str, Any]:
    """Utility function for converting the Algorand key-value schema into a python dictionary.

    Algorand store keys in base64 encoding and store values as either bytes or unsigned integers depending on the type. This function decodes this information into a more human friendly structure.

    Args:
        kv: Algorand key-value data structure to parse.

    Returns:
        The parsed key value dictionary.
    """
    res = {}
    for elem in kv:
        key = str(base64.b64decode(elem["key"]), encoding="ascii")
        if elem["value"]["type"] == 1:
            val = elem["value"]["bytes"]
        else:
            val = elem["value"]["uint"]
        res[key] = val
    return res


# Not used but may be handy for e.g. users of the lib when writing unit tests.
def serialize_uint64(values: Sequence[int]) -> str:
    _bytes = bytes(
        x
        for i in values
        for x in int.to_bytes(i, length=8, byteorder="big", signed=False)
    )
    return base64.b64encode(_bytes).decode("ascii")


def deserialize_uint64(data: str) -> Sequence[int]:
    decoded = base64.b64decode(data)
    return [
        int.from_bytes(decoded[offset : offset + 8], byteorder="big", signed=False)
        for offset in range(0, len(decoded), 8)
    ]
