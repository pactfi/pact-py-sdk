"""This example adds liquidity to the pool."""

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

# Opt-in for liquidity token.
opt_in_txn = pool.liquidity_asset.prepare_opt_in_tx(address)
sent_optin_txid = algod.send_transaction(opt_in_txn.sign(private_key))
print(f"OptIn transaction {sent_optin_txid}")

# Add liquidity
liquidity_addition = pool.prepare_add_liquidity(
    primary_asset_amount=1_000_000,
    secondary_asset_amount=500_000,
    slippage_pct=0.5,
)
add_liq_tx_group = liquidity_addition.prepare_tx_group(address=address)
signed_tx_group = add_liq_tx_group.sign(private_key)
algod.send_transactions(signed_tx_group)
print(f"Add liquidity transaction group {add_liq_tx_group.group_id}")
