"""This example fetches a farm and performs various user actions on it."""

# TODO validate that it works.

import algosdk
from algosdk.v2client.algod import AlgodClient

import pactsdk

private_key = algosdk.mnemonic.to_private_key("<mnemonic>")
address = algosdk.account.address_from_private_key(private_key)

algod = AlgodClient("<token>", "<url>")
pact = pactsdk.PactClient(algod)

farm = pact.farming.fetch_farm_by_id(123)
escrow = farm.fetch_escrow_by_address(address)

if escrow is None:
    # Deploy escrow.
    farm.refresh_suggested_params()

    deploy_txs = farm.prepare_deploy_escrow_txs(sender=address)
    algod.send_transaction(pactsdk.TransactionGroup(deploy_txs), private_key)

    txinfo = algod.pending_transaction_info(deploy_txs[-2].get_txid())
    escrow_id = txinfo["application-index"]

    escrow = farm.fetch_escrow_by_id(escrow_id)
    escrow.refresh_suggested_params()

# Inspect farm state.
print(farm.state)
"""
FarmState(
    staked_asset: <STAKED_COIN>,
    reward_assets: [<ASA>],
    total_rewards: {<ASA>: 0},
    claimed_rewards: {<ASA>: 0},
    pending_rewards: {<ASA>: 1000},
    next_rewards: {<ASA>: 0},
    rpt: {<ASA>: 0},
    duration: 10000,
    next_duration: 0,
    num_stakers: 0,
    total_staked: 0,
    updated_at: <datetime>,
    deprecated_at: <datetime>,
    admin: '<ADMIN_ADDRESS>',
    updater: '<ADMIN_ADDRESS>',
)
"""

# Need to be called before first transaction.
farm.refresh_suggested_params()


def update_farm():
    assert escrow
    update_txs = farm.build_update_with_opcode_increase_txs(escrow)
    group = pactsdk.TransactionGroup(update_txs)
    signed_tx = group.sign(private_key)
    algod.send_transaction(signed_tx)

    # Update farm state.
    farm.update_state()


update_farm()

# Stake tokens.
stake_txs = escrow.build_stake_txs(100_000)
group = pactsdk.TransactionGroup(stake_txs)
signed_group = group.sign(private_key)
algod.send_transactions(signed_group)
print(f"Stake transaction group {group.group_id}")

# Inspect user state.
user_state = escrow.fetch_user_state()
print(user_state)
"""
FarmUserState(
    escrow_id: 124,
    staked: 100_000,
    accrued_rewards: {<ASA>: 0},
    claimed_rewards: {<ASA>: 0},
    rpt: {<ASA>: 0.1},
)
"""

# Unstake.
unstake_txs = escrow.build_unstake_txs(100_000)
group = pactsdk.TransactionGroup(unstake_txs)
signed_tx = group.sign(private_key)
algod.send_transactions(signed_tx)
print(f"Unstake transaction group {group.group_id}")

# Claim
claim_tx = escrow.build_claim_rewards_tx()
signed_tx = claim_tx.sign(private_key)
algod.send_transactions(signed_tx)
print(f"Claim transaction {claim_tx.get_txid()}")
