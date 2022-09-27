# Farming

Pact utilizes an innovative architecture for farming called "micro farming". The idea behind it is that the system is split into two contracts:

**Farm** - contract resposible for accruing and sending the rewards to users.

**Escrow** - contract resposible for staking user tokens. Each user deploys his own escrow. It acts as a user's private escrow address.

The main benefit of the micro farming architecture is that the user has very strong guarantees of his funds safety. The escrow contract is very simple and easy to understand/audit. Only the user has access to funds deposited in the escrow and he can withdraw them at any moment. This is achieved with the Algorand's rekey mechanism.

Any potential bugs or exploits in the farm do not threaten the safety of user funds. In worst case scenario the user can lose the accrued rewards.

# Code examples

## Starting point for all examples

```py
from algosdk.v2client.algod import AlgodClient
import pactsdk

algod = AlgodClient('<token>', '<url>')
pact = pactsdk.PactClient(algod)
```

## How to fetch a farm / escrow?

```py
farm = pact.farming.fetch_farm_by_id(farm_id)
escrow = farm.fetch_escrow_by_id(escrow_id)

# If you don't know the escrow id you can...
escrow = farm.fetch_escrow_by_address(user_address)

# If you don't know the farm id you can...
escrow = pact.farming.fetch_escrow_by_id(escrow_id)
farm = escrow.farm
```

## How to create a new escrow?

```py
farm.refresh_suggested_params()

deploy_txs = farm.build_deploy_escrow_txs(sender=user_address)
sign_send_and_wait(pactsdk.TransactionGroup(deploy_txs), user_private_key)

txinfo = algod.pending_transaction_info(deploy_txs[-2].get_txid())
escrow_id = txinfo["application-index"]

escrow = farm.fetch_escrow_by_id(escrow_id)
escrow.refresh_suggested_params()
```

## How to find all escrows the user posses?

This fetches the account info and retrieves all apps matching the Escrow's approval program. It also fetches the accompanying farms.

```py
escrows = pact.farming.list_escrows(user_address)
```

If you already have the farms fetched, you can provide them as an argument. This will save you the extra algod requests to fetch the farms.

```py
escrows = pact.farming.list_escrows(user_address, farms=farms)
```

If you already have the account info and the farms fetched, you can list the escrows like below. This will not perform any algod requests and will return immediately.

```py
account_info = algod.account_info(user_address)
...
escrows = pact.farming.list_escrows_from_account_info(user_address, account_info, farms=farms)
```

## How to check farm's state?

To check check farm's global state.

```py
farm.update_state()
print(farm.state)
```

To check user's state.

```py
user_state = escrow.fetch_user_state()
print(user_state)
```

## How to stake / unstake?

```py
stake_txs = escrow.build_stake_txs(1_000_000)
sign_send_and_wait(pactsdk.TransactionGroup(stake_txs), user_private_key)
```

```py
unstake_txs = escrow.build_unstake_txs(1_000_000)
sign_send_and_wait(pactsdk.TransactionGroup(unstake_txs), user_private_key)
```

## How to check how many tokens are staked?

```py
user_state = escrow.fetch_user_state()
staked_amount = user_state.staked
```

or

```py
staked_amount = escrow.farm.staked_asset.get_holding(escrow.address)

# or if you want to reuse account_info and save some requests to algod.
account_info = algod.account_info(escrow.address)
...
staked_amount = escrow.farm.staked_asset.get_holding_from_account_info(account_info)
```

## How to claim rewards?

```py
# First update farm's local state.
update_txs = farm.build_update_with_opcode_increase_txs(escrow)

# Then claim the rewards.
claim_tx = escrow.build_claim_rewards_tx()

claim_tx_group = pactsdk.TransactionGroup([*update_txs, claim_tx])
sign_send_and_wait(claim_tx_group, user_private_key)
```

## How to estimate accrued rewards?

```py
user_state = escrow.fetch_user_state()
estimated_rewards = farm.estimate_accrued_rewards(datetime.now(), user_state)
```

## How to simulate farming?

```py
at_time = datetime.now() + timedelta(days=10)
simulated_rewards = farm.simulate_new_staker(at_time, staked_amount=1_000_000)
```

## How to use staked asset in e.g. Algorand's governance?

The users can you use the rekey mechanism to briefly gain full control over the escrow address.
First, you must rekey the escrow to your account, then perform any transactions you want on the escrow address and then, rekey the escrow back to the contract.
The SDK comes with a handy context manager that builds the transactions in the correct order for you.

```py
def build_governance_commit_tx(address, amount):
    # User custom code.
    ...

with escrow.rekey() as txs:
    gov_tx = build_governance_commit_tx(escrow.address, 1000)
    txs.append(gov_tx)

sign_send_and_wait(pactsdk.TransactionGroup(txs), user_private_key)
```

## How to destroy the escrow / regain access to staked funds in case of emergency?

The following code will close out the contract, transfer all algos and staked tokens to the user address, and delete the application.

```py
delete_txs = escrow.build_delete_and_clear_txs()
sign_send_and_wait(pactsdk.TransactionGroup(delete_txs), user_private_key)
```
