import base64
from dataclasses import dataclass
from decimal import Decimal as D
from typing import Any, Sequence


@dataclass
class AppInternalState:
    A: int
    B: int
    ASSET_A: int
    ASSET_B: int
    LTID: int
    L: int
    FEE_BPS: int


@dataclass
class PoolState:
    total_liquidity: int
    total_primary: int
    total_secondary: int
    primary_asset_price: D
    secondary_asset_price: D


def parse_global_pool_state(raw_state: list) -> AppInternalState:
    state = _parse_state(raw_state)
    asset_a, asset_b, fee_bps = deserialize_uint64(state.pop("CONFIG"))
    return AppInternalState(ASSET_A=asset_a, ASSET_B=asset_b, FEE_BPS=fee_bps, **state)


def _parse_state(kv: list) -> dict[str, Any]:
    # Transform algorand key-value schema into python dict with key value pairs
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
