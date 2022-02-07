from algosdk.v2client.algod import AlgodClient

import pactsdk

algod = AlgodClient("<token>", "<url>")  # provide options
pact = pactsdk.PactClient(algod)

algo = pact.fetch_asset(0)
jamnik = pact.fetch_asset(41409282)

pool = pact.fetch_pool(algo, jamnik)

print("State {pool.state}")
