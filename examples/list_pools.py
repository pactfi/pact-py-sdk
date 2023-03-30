"""This examples lists constant product pools created by the factory.
It will not list old pools created before introducing pool factory to the Pact architecture.
Each pool type require using a dedicated factory."""
import pprint

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

factory = pact.get_constant_product_pool_factory()

pool_params = factory.list_pools()
print('pools:')
pprint.pprint(pool_params)

# To fully fetch the pool of choice...
pool = factory.fetch_pool(pool_params[0])
print('Selected pool:')
pprint.pprint(pool)
