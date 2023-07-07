"""This example performs a basic actions on a lending pool."""

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

FOLKS_POOL_A = 147169673  # ALGO
FOLKS_POOL_B = 147170678  # USDC

folks_lending_pool_ids = sorted([FOLKS_POOL_A, FOLKS_POOL_B])

pk = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(pk)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod, network="testnet")

# Folks pools.
print("Fetching folks lending pools...")
primary_folks_pool = pact.fetch_folks_lending_pool(folks_lending_pool_ids[0])
secondary_folks_pool = pact.fetch_folks_lending_pool(folks_lending_pool_ids[1])

# Pact pool.
print("Fetching or creating pact pool...")
factory = pact.get_constant_product_pool_factory()
pool_build_params = pactsdk.PoolBuildParams(
    primary_asset_id=primary_folks_pool.f_asset.index,
    secondary_asset_id=secondary_folks_pool.f_asset.index,
    fee_bps=2,
)
pact_pool, created = factory.build_or_get(
    sender=address,
    pool_build_params=pool_build_params,
    signer=lambda tx_group: tx_group.sign(pk),
)

# Make an adapter.
lending_pool_adapter = pact.get_folks_lending_pool_adapter(
    primary_lending_pool=primary_folks_pool,
    secondary_lending_pool=secondary_folks_pool,
    pact_pool=pact_pool,
)

if created:
    # Adapter opt-in to all the assets.
    print("Opting in adapter to assets...")
    asset_ids = [
        primary_folks_pool.original_asset.index,
        secondary_folks_pool.original_asset.index,
        primary_folks_pool.f_asset.index,
        secondary_folks_pool.f_asset.index,
        pact_pool.liquidity_asset.index,
    ]
    tx_group = lending_pool_adapter.prepare_opt_in_to_asset_tx_group(address, asset_ids)
    algod.send_transactions(tx_group.sign(pk))
    print(tx_group.group_id)
    print()

# Add liquidity.
print("Adding liquidity...")
liquidity_addition = lending_pool_adapter.prepare_add_liquidity(100_000, 100_000, 0.5)
tx_group = lending_pool_adapter.prepare_add_liquidity_tx_group(
    address, liquidity_addition
)
algod.send_transactions(tx_group.sign(pk))
print(tx_group.group_id)
print()

# Swap.
print("Swapping...")
swap = lending_pool_adapter.prepare_swap(
    primary_folks_pool.original_asset, amount=100_000, slippage_pct=100
)
tx_group = lending_pool_adapter.prepare_swap_tx_group(swap, address)
algod.send_transactions(tx_group.sign(pk))
print(tx_group.group_id)
print()

# Remove liquidity.
print("Removing liquidity...")
tx_group = lending_pool_adapter.prepare_remove_liquidity_tx_group(address, 20_000)
algod.send_transactions(tx_group.sign(pk))
print(tx_group.group_id)
