# Farming

Pact utilizes an innovative architecture for farming called "micro farming". The idea behind it is that the system is split into two contracts:

**Farm** - contract resposible for accruing and sending the rewards to users.

**Escrow** - contract resposible for staking user tokens. Each user deploys his own escrow. It acts as a user's private escrow address.

The main benefit of the micro farming architecture is that the user has very strong guarantees of his funds safety. The escrow contract is very simple and easy to understand/audit. Only the user has access to funds deposited in the escrow and he can withdraw them at any moment.

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

deploy_txs = farm.prepare_deploy_escrow_txs(sender=user_address)
sign_send_and_wait(pactsdk.TransactionGroup(deploy_txs), user_private_key)

txinfo = algod.pending_transaction_info(deploy_txs[-2].get_txid())
escrow_id = txinfo["application-index"]

escrow = farm.fetch_escrow_by_id(escrow_id)
escrow.refresh_suggested_params()
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

```py
send_message_tx = testbed.escrow.build_send_message_tx(
    sender, "some message required by the Foundation"
)
sign_send_and_wait(send_message_tx, sender, user_private_key)
```

## How to destroy the escrow / regain access to staked funds in case of emergency?

The following code will close out the contract, transfer all algos and staked tokens to the user address, and delete the application.

```py

# Exit the farm.
# This will claim all staked tokens and algos locked in the escrow back to the user account and delete the escrow.
# It requires all the rewards to bo claimed, fails otherwise.
exit_tx = escrow.build_exit_tx()
delete_tx = escrow.build_delete_tx()
exit_and_delete_group = pactsdk.TransactionGroup([exit_tx, delete_tx])
sign_send_and_wait(exit_and_delete_group, user_private_key)

# Force exit the farm.
# Claim all the rewards before exiting from the farm or you will lose your rewards.
# This will claim all staked tokens and algos locked in the escrow back to the user account and delete the escrow.
exit_tx = escrow.build_force_exit_tx()
delete_tx = escrow.build_delete_tx()
exit_and_delete_group = pactsdk.TransactionGroup([exit_tx, delete_tx])
sign_send_and_wait(exit_and_delete_group, user_private_key)
```
