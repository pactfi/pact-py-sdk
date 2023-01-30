import base64
from copy import copy
from typing import Any

from algosdk import transaction
from Cryptodome.Hash import SHA512


def sp_fee(sp: transaction.SuggestedParams, fee: int) -> transaction.SuggestedParams:
    """
    Get a copy of suggested params but with a different fee.
    """
    sp = copy(sp)
    sp.flat_fee = True
    sp.fee = fee
    return sp


def parse_app_state(kv: list) -> dict[str, Any]:
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


def get_selector(method_signature: str) -> bytes:
    hash_ = SHA512.new(truncate="256")
    hash_.update(method_signature.encode("utf-8"))
    return hash_.digest()[:4]
