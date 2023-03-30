"""This example fetches a pool and reads its state."""

from algosdk.v2client.algod import AlgodClient

import pactsdk

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

algo = pact.fetch_asset(0)
usdc = pact.fetch_asset(31566704)

pool = pact.fetch_pools_by_assets(algo, usdc)[0]

print(f"State {pool.state}")
