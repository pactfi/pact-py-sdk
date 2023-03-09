import base64
from copy import copy
from typing import Any

import algosdk
from Cryptodome.Hash import SHA512


def sp_fee(
    sp: algosdk.transaction.SuggestedParams, fee: int
) -> algosdk.transaction.SuggestedParams:
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


def get_box_min_balance(len_box_name: int, box_size: int) -> int:
    # https://developer.algorand.org/articles/smart-contract-storage-boxes/
    assert len_box_name <= 64
    return 2500 + 400 * (len_box_name + box_size)


def get_last_round(algod: algosdk.v2client.algod.AlgodClient) -> int:
    return algod.status().get("last-round")


# Function from Algorand Inc.
def wait_for_confirmation(algod: algosdk.v2client.algod.AlgodClient, txid: str) -> dict:
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = get_last_round(algod)
    txinfo = algod.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        last_round += 1
        algod.status_after_block(last_round)
        txinfo = algod.pending_transaction_info(txid)
    return txinfo
