"""This example deploys a new pool if pool with the given params doesn't exist yet."""
import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

factory = pact.get_constant_product_pool_factory()

pool_params = pactsdk.PoolBuildParams(
    primary_asset_id=0,
    secondary_asset_id=14111329,
    fee_bps=100,
)

pool, created = factory.build_or_get(
    sender=address,
    pool_build_params=pool_params,
    signer=lambda tx_group: tx_group.sign(private_key),
)
print("New pool created." if created else "Pool with specified params already exists.")
print(pool)
