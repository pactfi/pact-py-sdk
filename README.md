# Pact Python SDK

Python SDK for Pact smart contracts.

What is covered by the library:

- Fetching pools
- Opt-in for assets
- Managing liquidity
- Inspecting pools state
- Making swaps

Signing and sending transactions is not covered by the library. The provided examples use algosdk directly to send the transactions.

# Installation

`pip install pactsdk`

# Basic usage

**CAUTION** - The library uses integers for asset amounts e.g. microalgos instead of algos so if you want to send 1 algo, you need to specify it as 1_000_000.

Create a Pact client.

```py
from algosdk.v2client.algod import AlgodClient
import pactsdk

algod = AlgodClient(token, url)
pact = pactsdk.PactClient(algod)
```

Optionally you can specify custom Pact API url. By default it directs to production API.

```py
pact = pactsdk.PactClient(algod, pact_api_url="https://api.testnet.pact.fi")
```

Fetching a pool.

```py
algo = pact.fetch_asset(0)
other_coin = pact.fetch_asset(8949213)

pool = pact.fetch_pool(algo, other_coin) # The pool will be fetched regardless of assets order.
```

Fetching a pool also accepts optional parameters.

```py
pool = pact.fetch_pool(
  algo,
  other_coin,
  app_id=456321,  # Use if the pool is not visible in the Pact API.
  fee_bps=30,  # Use if your custom contract uses non-default fee.
)
```

You can list all pools from the Pact API.

```py
pools = pact.list_pools()
print(pools)
# {
#   "count": 19,
#   "next": "http://api.pact.fi/api/pools?page=2",
#   "previous": None,
#   "results": [...],
# }

# The listing uses pagination and filtering.
pools = pact.list_pools(
  page=2,
  primary_asset__algoid=9843123,
)
```

Before making the transactions you need to opt-in for the assets. There's no need to opt-in for algo.

```py
import algosdk

private_key = algosdk.mnemonic.to_private_key('<mnemonic>')
address = algosdk.account.address_from_private_key(private_key)

def opt_in(asset):
  is_opted_in = asset.is_opted_in(address)
  if not is_opted_in
    opt_in_tx = asset.prepare_opt_in_tx(address)
    signed_tx = opt_in_tx.sign(private_key)
    algod.send_transaction(signed_tx)
  }
}

opt_in(pool.primary_asset)
opt_in(pool.secondary_asset)
opt_in(pool.liquidity_asset) # Needed if you want to manage the liquidity.
```

Check the current pool state.

```py
print(pool.state)
# PoolState(
#   total_liquidity=900000,
#   total_primary=956659,
#   total_secondary=849972,
#   primary_asset_price=Decimal(0.8884795940873393),
#   secondary_asset_price=Decimal(1.1255182523659604),
# )
```

Explicit pool state update is necessary periodically and after each pool operation.

```py
pool.update_state()
pool.state  # Now holds fresh values.
```

Managing the liquidity.

```py
# Add liquidity.
add_liq_tx_group = pool.prepare_add_liquidity_tx(
  address=address,
  primary_asset_amount=100_000,
  secondary_asset_amount=50_000,
);
signed_add_liq_tx_group = add_liq_tx_group.sign(private_key)
algod.send_transactions(signed_add_liq_tx_group)

# Remove liquidity.
remove_liq_tx_group = pool.prepare_remove_liquidity_tx(
  address=address,
  amount=100_000,
)
signed_remove_liq_tx_group = remove_liq_tx_group.sign(private_key)
algod.send_transactions(signed_remove_liq_tx_group)
```

Making a swap.

```py
swap = pool.prepare_swap(
  asset=algo,
  amount=200_000,
  slippage_pct=2,
)

# You can inspect swap effect before submitting the transaction.
print(swap.effect)
# SwapEffect(
#     amount_out=200000,
#     amount_in=146529,
#     minimum_amount_in=143598,
#     fee=441,
#     price=Decimal(0.73485),
#     primary_asset_price_after_swap=Decimal("0.6081680080300244"),
#     secondary_asset_price_after_swap=Decimal("1.6442824791774173"),
#     primary_asset_price_change_pct=Decimal("-31.549580645715963"),
#     secondary_asset_price_change_pct=Decimal("46.091142966447585"),
# )

# Let's submit the swap.
swap_tx_group = swap.prepare_tx(address)
signed_tx_group = swap_tx_group.sign_txn(private_key)
algod.send_transactions(signed_tx_group)
```

Look for more [examples](examples).

# Development

- `poetry install`

Development requires [Pact contracts V1](https://github.com/pactfi/algorand-testbed) to be checked out.

- `git clone git@github.com:pactfi/algorand-testbed.git`
- `cd algorand-testbed`
- `poetry install`
- `docker compose up -d`
- `cd ..`

## Building

- `poetry build`

You can install the package locally with
`pip install dist/pactsdk-<version>.whl`

Validate the installation `python -c "import pactsdk; print(pactsdk.__version__)"`

## Running tests

- `poetry run pytest`
