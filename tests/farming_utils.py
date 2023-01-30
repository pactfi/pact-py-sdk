from contextlib import contextmanager
from dataclasses import dataclass

from algosdk import transaction

import pactsdk

from .utils import (
    Account,
    algod,
    create_asset,
    deploy_contract,
    new_account,
    sign_and_send,
    wait_rounds,
)


def deploy_farm(account: Account, staked_asset_id: int):
    return deploy_contract(
        account,
        [
            "farm",
            f"--staked-asset-id={staked_asset_id}",
            f"--gas-station-id={pactsdk.get_gas_station().app_id}",
            f"--admin={account.address}",
        ],
    )


@dataclass
class FarmingTestBed:
    __test__ = False

    admin_account: Account
    user_account: Account
    pact: pactsdk.PactClient
    staked_asset: pactsdk.Asset
    reward_asset: pactsdk.Asset
    algo: pactsdk.Asset
    farm: pactsdk.Farm
    escrow: pactsdk.Escrow

    def wait_rounds_and_update_farm(self, rounds: int):
        assert rounds >= 1
        wait_rounds(rounds - 1, self.user_account)
        update_farm(self.escrow, self.user_account)

    def deposit_rewards(self, rewards: pactsdk.FarmingRewards[int], duration: int):
        deposit_rewards_txs = self.farm.admin_build_deposit_rewards_txs(
            rewards, duration
        )
        sign_and_send(pactsdk.TransactionGroup(deposit_rewards_txs), self.admin_account)
        self.farm.update_state()

    def stake(self, amount: int):
        stake_txs = self.escrow.build_stake_txs(amount)
        sign_and_send(pactsdk.TransactionGroup(stake_txs), self.user_account)

    def unstake(self, amount: int):
        unstake_txs = self.escrow.build_unstake_txs(amount)
        sign_and_send(pactsdk.TransactionGroup(unstake_txs), self.user_account)

    def claim(self):
        claim_tx = self.escrow.build_claim_rewards_tx()
        sign_and_send(claim_tx, self.user_account)

    def make_asset(self, name: str):
        asset = self.pact.fetch_asset(create_asset(self.admin_account, name=name))
        optin_tx = asset.build_opt_in_tx(
            self.user_account.address, self.farm.suggested_params
        )
        sign_and_send(optin_tx, self.user_account)
        return asset

    @contextmanager
    def assert_rewards(
        self,
        rewards: pactsdk.FarmingRewards[int] = None,
        address: str = None,
    ):
        if address is None:
            address = self.user_account.address

        old_user_balance = fetch_user_assets_balance(self.farm, address)

        if rewards is None:
            user_state = self.farm.fetch_user_state(address)
            assert user_state
            rewards = user_state.accrued_rewards

        yield

        new_user_balance = fetch_user_assets_balance(self.farm, address)
        for asset, amount in new_user_balance.items():
            if asset.index == 0:
                # Cannot test ALGO in a reliable way because of farm rewards being distributed.
                continue
            expected_amount = old_user_balance.get(asset, 0) + rewards.get(asset, 0)
            assert (
                amount == expected_amount
            ), f"Expected {expected_amount} {asset}, got {amount} {asset}."


def make_fresh_farming_testbed():
    admin_account = new_account()
    pact = pactsdk.PactClient(algod)

    algo = pact.fetch_asset(0)

    staked_asset = pact.fetch_asset(create_asset(admin_account, name="ASA_STK"))
    reward_asset = pact.fetch_asset(create_asset(admin_account, name="ASA_REW"))

    suggested_params = algod.suggested_params()

    farm_id = deploy_farm(admin_account, staked_asset.index)
    farm = pact.farming.fetch_farm_by_id(farm_id)
    farm.set_suggested_params(suggested_params)

    fund_algo_tx = transaction.PaymentTxn(
        sender=admin_account.address,
        receiver=farm.app_address,
        amt=100_000,
        sp=suggested_params,
    )
    sign_and_send(fund_algo_tx, admin_account)

    user_account, escrow = make_new_account_and_escrow(
        farm, admin_account, [reward_asset]
    )

    return FarmingTestBed(
        admin_account=admin_account,
        user_account=user_account,
        pact=pact,
        staked_asset=staked_asset,
        reward_asset=reward_asset,
        algo=algo,
        farm=farm,
        escrow=escrow,
    )


def make_new_account_and_escrow(
    farm: pactsdk.Farm, admin_account: Account, reward_assets: list[pactsdk.Asset]
) -> tuple[Account, pactsdk.Escrow]:
    user_account = make_new_account_for_farm(farm, admin_account, reward_assets)

    escrow = deploy_escrow_for_account(farm, user_account, farm.suggested_params)
    escrow.set_suggested_params(farm.suggested_params)

    return user_account, escrow


def make_new_account_for_farm(
    farm: pactsdk.Farm, admin_account: Account, reward_assets: list[pactsdk.Asset]
):
    user_account = new_account()

    # Opt-in user to assets.
    for asset in [farm.staked_asset, *reward_assets]:
        if asset.index != 0:
            optin_tx = asset.build_opt_in_tx(
                user_account.address, farm.suggested_params
            )
            sign_and_send(optin_tx, user_account)

    # Transfer staking asset to the user.
    transfer_tx = farm.staked_asset.build_transfer_tx(
        sender=admin_account.address,
        receiver=user_account.address,
        amount=1_000_000,
        suggested_params=farm.suggested_params,
    )
    sign_and_send(transfer_tx, admin_account)

    return user_account


def deploy_escrow_for_account(
    farm: pactsdk.Farm,
    user_account: Account,
    suggested_params: transaction.SuggestedParams,
) -> pactsdk.Escrow:
    escrow_approval_program = pactsdk.fetch_escrow_approval_program(algod, farm.app_id)
    deploy_txs = pactsdk.build_deploy_escrow_txs(
        sender=user_account.address,
        farm_app_id=farm.app_id,
        staked_asset_id=farm.staked_asset.index,
        suggested_params=suggested_params,
        approval_program=escrow_approval_program,
    )
    sign_and_send(pactsdk.TransactionGroup(deploy_txs), user_account)
    txinfo = algod.pending_transaction_info(deploy_txs[-2].get_txid())
    app_id = txinfo["application-index"]

    escrow = farm.fetch_escrow_by_id(app_id)
    assert escrow
    return escrow


def update_farm(escrow: pactsdk.Escrow, account: Account):
    escrow.farm.refresh_suggested_params()

    update_txs = escrow.farm.build_update_with_opcode_increase_txs(escrow)
    sign_and_send(pactsdk.TransactionGroup(update_txs), account)

    escrow.farm.update_state()


def fetch_user_assets_balance(
    farm: pactsdk.Farm, address: str
) -> dict[pactsdk.Asset, int]:
    account_info = farm.algod.account_info(address)
    return {
        asset: asset.get_holding_from_account_info(account_info) or 0
        for asset in farm.state.reward_assets + [farm.staked_asset]
    }
