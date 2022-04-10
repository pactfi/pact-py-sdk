"""
Python package pactsdk provides a software development kit for interfacing to Pact, a decentralized Automated market maker on the Algorand protcol.
(See https://pact.fi for more details)

The python sdk provides a set of modules on top of the algorand python sdk for interacting with liquidity pools and trading swaps.
Clients can use the python sdk to enhance their trading experience with Pact.

Typical usage example:
```
import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")  # provide options
pact = pactsdk.PactClient(algod)

algo = pact.fetch_asset(0)
jamnik = pact.fetch_asset(41409282)

opt_in_txn = jamnik.prepare_opt_in_tx(address)
sent_optin_txid = algod.send_transaction(opt_in_txn.sign(private_key))
print(f"OptIn transaction {sent_optin_txid}")

pool = pact.fetch_pools_by_assets(algo, jamnik)[0]

swap = pool.prepare_swap(
    asset=algo,
    amount=100_000,
    slippage_pct=2,
)
swap_tx_group = swap.prepare_tx(address)
signed_txs_group = swap_tx_group.sign(private_key)
sent_txid = algod.send_transactions(signed_txs_group
```
"""
__version__ = "0.1.0"

from .asset import Asset  # noqa
from .client import PactClient  # noqa
from .exceptions import PactSdkError  # noqa
from .pool import Pool, PoolState  # noqa
from .swap import Swap, SwapEffect  # noqa
from .transaction_group import TransactionGroup  # noqa
