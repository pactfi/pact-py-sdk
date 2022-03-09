import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")  # provide options
pact = pactsdk.PactClient(algod)

algo = pact.fetch_asset(0)
jamnik = pact.fetch_asset(41409282)

# Opt-in for jamnik.
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
sent_txid = algod.send_transactions(signed_txs_group)

print(f"Transaction {sent_txid}")
