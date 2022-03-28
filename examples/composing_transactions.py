"""This example performs asset opt-in and a swap in a single atomic group."""

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod)

pool = pact.fetch_pool_by_id(620995314)  # ALGO/USDC

suggested_params = algod.suggested_params()

opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(address)

swap = pool.prepare_swap(
    asset=pool.primary_asset,
    amount=100_000,
    slippage_pct=2,
)
swap_txs = pool.build_swap_txs(swap, address, suggested_params)

txs = [opt_in_tx, *swap_txs]

group = pactsdk.TransactionGroup(txs)
signed_group = group.sign(private_key)
algod.send_transactions(signed_group)

print(f"Transaction group {group.group_id}")
