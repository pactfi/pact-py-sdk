"""This example performs asset opt-in and add liquidity in a single atomic group."""

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

pool = pact.fetch_pool_by_id(620995314)  # ALGO/USDC

suggested_params = algod.suggested_params()

opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(address)

liquidity_addition = pool.prepare_add_liquidity(
    primary_asset_amount=100_000,
    secondary_asset_amount=200_000,
)
add_liquidity_txs = pool.build_add_liquidity_txs(
    address="<address>",
    liquidity_addition=liquidity_addition,
    suggested_params=suggested_params,
)

txs = [opt_in_tx, *add_liquidity_txs]

group = pactsdk.TransactionGroup(txs)
signed_group = group.sign(private_key)
algod.send_transactions(signed_group)

print(f"Transaction group {group.group_id}")
