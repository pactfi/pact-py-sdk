import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient()  # provide options
pact = pactsdk.PactClient(algod)

algo = pact.fetch_asset(0)
jamnik = pact.fetch_asset(41409282)

pool = pact.fetch_pools_by_assets(algo, jamnik)[0]

# Opt-in for liquidity token.
opt_in_txn = pool.liquidity_asset.prepare_opt_in_tx(address)
sent_optin_txid = algod.send_transaction(opt_in_txn.sign(private_key))
print(f"OptIn transaction {sent_optin_txid}")

add_liq_tx_group = pool.prepare_add_liquidity_tx(
    address=address,
    primary_asset_amount=1_000_000,
    secondary_asset_amount=500_000,
)
signed_tx_group = add_liq_tx_group.sign(private_key)
sent_txid = algod.send_transactions(signed_tx_group)

print(f"Transaction {sent_txid}")
