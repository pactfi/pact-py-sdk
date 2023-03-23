"""This example performs a swap on a pool."""

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

algo = pact.fetch_asset(0)
usdc = pact.fetch_asset(31566704)
pool = pact.fetch_pools_by_assets(algo, usdc)[0]

# Opt-in for usdc.
opt_in_txn = usdc.prepare_opt_in_tx(address)
sent_optin_txid = algod.send_transaction(opt_in_txn.sign(private_key))
print(f"Opt-in transaction {sent_optin_txid}")

# Do a swap.
swap = pool.prepare_swap(
    asset=algo,
    amount=100_000,
    slippage_pct=2,
)
swap_tx_group = swap.prepare_tx_group(address)
signed_group = swap_tx_group.sign(private_key)
algod.send_transactions(signed_group)
print(f"Swap transaction group {swap_tx_group.group_id}")
