import datetime

import algosdk
import pytest
from algosdk import transaction

import pactsdk
from pactsdk.asset import ASSETS_CACHE

from .farming_utils import (
    deploy_farm,
    make_fresh_farming_testbed,
    make_new_account_and_escrow,
    make_new_account_for_farm,
    update_farm,
)
from .matchers import Any
from .utils import (
    algod,
    create_asset,
    get_last_block,
    new_account,
    sign_and_send,
    wait_rounds,
)


@pytest.fixture(autouse=True)
def auto_gas_station(gas_station):
    pass


def test_farming_fetch_farm():
    testbed = make_fresh_farming_testbed()

    user_1, escrow_1 = testbed.user_account, testbed.escrow
    user_2, escrow_2 = make_new_account_and_escrow(
        testbed.farm, testbed.admin_account, [testbed.reward_asset]
    )

    assert escrow_1 != escrow_2

    # Fetch farm and escrow.
    escrow = testbed.pact.farming.fetch_escrow_by_id(escrow_1.app_id)
    assert escrow.app_id == escrow_1.app_id
    assert escrow.farm.app_id == testbed.farm.app_id

    # Fetch only the farm.
    farm = testbed.pact.farming.fetch_farm_by_id(testbed.farm.app_id)
    assert farm.app_id == testbed.farm.app_id

    # Fetch escrow from the farm.

    # By id.
    escrow = farm.fetch_escrow_by_id(escrow_1.app_id)
    assert escrow == escrow_1
    escrow = farm.fetch_escrow_by_id(escrow_2.app_id)
    assert escrow == escrow_2

    # By address.
    escrow = farm.fetch_escrow_by_address(user_1.address)
    assert escrow == escrow_1
    escrow = farm.fetch_escrow_by_address(user_2.address)
    assert escrow == escrow_2

    # From account info.
    info_1 = testbed.pact.algod.account_info(user_1.address)
    escrow = testbed.farm.fetch_escrow_from_account_info(info_1)
    assert escrow == escrow_1
    info_2 = testbed.pact.algod.account_info(user_2.address)
    escrow = testbed.farm.fetch_escrow_from_account_info(info_2)
    assert escrow == escrow_2


def test_farming_farm_state():
    testbed = make_fresh_farming_testbed()

    last_block = get_last_block()

    assert testbed.farm.internal_state == pactsdk.FarmInternalState(
        staked_asset_id=testbed.staked_asset.index,
        reward_asset_ids=[],
        distributed_rewards=[0, 0, 0, 0, 0, 0, 0],
        claimed_rewards=[0, 0, 0, 0, 0, 0, 0],
        pending_rewards=[0, 0, 0, 0, 0, 0, 0],
        next_rewards=[0, 0, 0, 0, 0, 0, 0],
        rpt_frac=[0, 0, 0, 0, 0, 0, 0],
        rpt=[0, 0, 0, 0, 0, 0, 0],
        duration=0,
        next_duration=0,
        num_stakers=0,
        total_staked=0,
        updated_at=last_block - 6,
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )
    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[],
        distributed_rewards={},
        claimed_rewards={},
        pending_rewards={},
        next_rewards={},
        rpt={},
        duration=0,
        next_duration=0,
        num_stakers=0,
        total_staked=0,
        updated_at=datetime.datetime.fromtimestamp(last_block - 6),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    testbed.deposit_rewards({testbed.reward_asset: 2000}, duration=100)
    last_block = get_last_block()

    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[testbed.reward_asset],
        distributed_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 0},
        pending_rewards={testbed.reward_asset: 2000},
        next_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0},
        duration=100,
        next_duration=0,
        num_stakers=0,
        total_staked=0,
        updated_at=datetime.datetime.fromtimestamp(last_block),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    testbed.stake(1000)
    testbed.farm.update_state()
    last_block = get_last_block()

    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[testbed.reward_asset],
        distributed_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 0},
        pending_rewards={testbed.reward_asset: 2000},
        next_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0},
        duration=100,
        next_duration=0,
        num_stakers=1,
        total_staked=1000,
        updated_at=datetime.datetime.fromtimestamp(last_block),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=1000,
        accrued_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0},
    )


def test_farming_happy_path():
    testbed = make_fresh_farming_testbed()

    # Deposit rewards.
    testbed.deposit_rewards({testbed.reward_asset: 2000}, duration=100)

    # Stake.
    testbed.stake(1000)
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 1000

    # Check farm and user state.
    testbed.farm.update_state()
    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=1000,
        accrued_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0},
    )
    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[testbed.reward_asset],
        distributed_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 0},
        pending_rewards={testbed.reward_asset: 2000},
        next_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0},
        duration=100,
        next_duration=0,
        num_stakers=1,
        total_staked=1000,
        updated_at=Any(datetime.datetime),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    # Wait some time and unstake all.
    wait_rounds(10, testbed.user_account)
    testbed.unstake(1000)
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 0

    # Check the state.
    testbed.farm.update_state()
    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=0,
        accrued_rewards={testbed.reward_asset: 219},
        claimed_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0.22},
    )
    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[testbed.reward_asset],
        distributed_rewards={testbed.reward_asset: 220},
        claimed_rewards={testbed.reward_asset: 0},
        pending_rewards={testbed.reward_asset: 1780},
        next_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0.22},
        duration=89,
        next_duration=0,
        num_stakers=0,
        total_staked=0,
        updated_at=Any(datetime.datetime),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    # Claim rewards.
    with testbed.assert_rewards():
        testbed.claim()

    # Accrued rewards are empty.
    testbed.farm.update_state()
    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=0,
        accrued_rewards={testbed.reward_asset: 0},
        claimed_rewards={testbed.reward_asset: 219},
        rpt={testbed.reward_asset: 0.22},
    )
    assert testbed.farm.state == pactsdk.FarmState(
        staked_asset=testbed.staked_asset,
        reward_assets=[testbed.reward_asset],
        distributed_rewards={testbed.reward_asset: 220},
        claimed_rewards={testbed.reward_asset: 219},
        pending_rewards={testbed.reward_asset: 1780},
        next_rewards={testbed.reward_asset: 0},
        rpt={testbed.reward_asset: 0.22},
        duration=89,
        next_duration=0,
        num_stakers=0,
        total_staked=0,
        updated_at=Any(datetime.datetime),
        admin=testbed.admin_account.address,
        updater=testbed.admin_account.address,
        version=100,
    )

    assert testbed.reward_asset.get_holding(testbed.farm.app_address) == 1781
    assert testbed.reward_asset.get_holding(testbed.user_account.address) == 219


def test_farming_stake_and_unstake():
    testbed = make_fresh_farming_testbed()

    testbed.deposit_rewards({testbed.reward_asset: 2000}, duration=100)

    testbed.stake(1000)
    testbed.farm.update_state()
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 1000
    assert testbed.farm.state.total_staked == 1000

    testbed.unstake(400)
    testbed.farm.update_state()
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 600
    assert testbed.farm.state.total_staked == 600

    testbed.unstake(500)
    testbed.farm.update_state()
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 100
    assert testbed.farm.state.total_staked == 100

    # Cannot unstake more that is staked.
    with pytest.raises(algosdk.error.AlgodHTTPError):
        testbed.unstake(200)

    # Can unstake everything.
    testbed.unstake(100)
    testbed.farm.update_state()
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 0
    assert testbed.farm.state.total_staked == 0


def test_farming_exit_and_delete():
    testbed = make_fresh_farming_testbed()
    testbed.deposit_rewards({testbed.reward_asset: 1000}, duration=100)

    testbed.stake(1_000_000)
    testbed.wait_rounds_and_update_farm(5)

    assert testbed.farm.state.distributed_rewards == {testbed.reward_asset: 50}
    assert testbed.farm.state.total_staked == 1_000_000
    assert testbed.farm.state.num_stakers == 1

    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 1_000_000
    assert testbed.algo.get_holding(testbed.escrow.address) == 200_000

    # Claim and unstake are required before exiting.
    exit_tx = testbed.escrow.build_exit_tx()
    delete_tx = testbed.escrow.build_delete_tx()
    exit_and_delete_group = pactsdk.TransactionGroup([exit_tx, delete_tx])
    with pytest.raises(algosdk.error.AlgodHTTPError):
        sign_and_send(exit_and_delete_group, testbed.user_account)

    # Do claim and unstake.
    unstake_txs = testbed.escrow.build_unstake_txs(1_000_000)
    claim_tx = testbed.escrow.build_claim_rewards_tx()
    sign_and_send(
        pactsdk.TransactionGroup([*unstake_txs, claim_tx]), testbed.user_account
    )

    user_algo_amount = testbed.algo.get_holding(testbed.user_account.address)

    # Close out and delete the micro farm.
    sign_and_send(exit_and_delete_group, testbed.user_account)

    # Make sure the escrow address is cleared.
    assert testbed.staked_asset.get_holding(testbed.escrow.address) is None
    assert testbed.algo.get_holding(testbed.escrow.address) == 0

    # Make sure all algos are claimed by the user account.
    assert (
        testbed.algo.get_holding(testbed.user_account.address)
        == user_algo_amount + 200_000 - 4000  # + locked amount - fee
    )


def test_farming_force_exit_and_delete():
    testbed = make_fresh_farming_testbed()
    testbed.deposit_rewards({testbed.reward_asset: 1000}, duration=100)

    testbed.stake(1_000_000)
    testbed.wait_rounds_and_update_farm(5)

    assert testbed.farm.state.distributed_rewards == {testbed.reward_asset: 50}
    assert testbed.farm.state.total_staked == 1_000_000
    assert testbed.farm.state.num_stakers == 1

    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 1_000_000
    assert testbed.algo.get_holding(testbed.escrow.address) == 200_000

    user_algo_amount = testbed.algo.get_holding(testbed.user_account.address)
    user_staked_amount = testbed.staked_asset.get_holding(testbed.user_account.address)

    # Close out and delete the micro farm. Unstake is not required when doing force_exit.
    exit_tx = testbed.escrow.build_force_exit_tx()
    delete_tx = testbed.escrow.build_delete_tx()
    sign_and_send(pactsdk.TransactionGroup([exit_tx, delete_tx]), testbed.user_account)

    # Make sure the escrow address is cleared.
    assert testbed.staked_asset.get_holding(testbed.escrow.address) is None
    assert testbed.algo.get_holding(testbed.escrow.address) == 0

    # Make sure all algos and staked tokens are claimed by the user account.
    assert (
        testbed.algo.get_holding(testbed.user_account.address)
        == user_algo_amount + 200_000 - 4000  # + locked amount - fee
    )
    assert (
        testbed.staked_asset.get_holding(testbed.user_account.address)
        == user_staked_amount + 1_000_000
    )


def test_farming_estimate_rewards():
    testbed = make_fresh_farming_testbed()
    testbed.stake(100)
    user_state = testbed.escrow.fetch_user_state()

    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=5)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {}

    testbed.deposit_rewards({testbed.reward_asset: 1000}, duration=10)

    # No next rewards, estimate zero second.
    at_time = testbed.farm.state.updated_at
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 0
    }
    assert testbed.farm.simulate_new_staker(at_time, 100) == {testbed.reward_asset: 0}

    # No next rewards, estimate first second.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=1)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 100
    }
    assert testbed.farm.simulate_new_staker(at_time, 100) == {testbed.reward_asset: 50}

    # No next rewards, estimate middle of first cycle.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=5)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 500
    }
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 45}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {testbed.reward_asset: 250}
    assert testbed.farm.simulate_new_staker(at_time, 200) == {testbed.reward_asset: 333}
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 476
    }

    # No next rewards, estimate end of first cycle.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=10)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 1000  # no future extrapolation for estimate.
    }
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 90}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {testbed.reward_asset: 500}
    assert testbed.farm.simulate_new_staker(at_time, 200) == {testbed.reward_asset: 666}
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 952
    }

    # No next rewards, estimate future cycles.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=55)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 1000
    }
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 499}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {
        testbed.reward_asset: 2750
    }
    assert testbed.farm.simulate_new_staker(at_time, 200) == {
        testbed.reward_asset: 3666
    }
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 5237
    }

    # Deposit next rewards.
    testbed.deposit_rewards({testbed.reward_asset: 5000}, duration=20)

    # Next rewards, estimate middle of first cycle. 4 seconds instead of 5 because deposit_rewards is one second.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=4)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 500
    }
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=5)
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 45}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {testbed.reward_asset: 250}
    assert testbed.farm.simulate_new_staker(at_time, 200) == {testbed.reward_asset: 333}
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 476
    }

    # Next rewards, estimate middle of next cycle.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=19)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 3500
    }
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=20)
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 331}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {
        testbed.reward_asset: 1825
    }
    assert testbed.farm.simulate_new_staker(at_time, 200) == {
        testbed.reward_asset: 2433
    }
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 3476
    }

    # Next rewards, estimate future cycles.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=54)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 6000
    }
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=55)
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 1125}
    assert testbed.farm.simulate_new_staker(at_time, 100) == {
        testbed.reward_asset: 6200
    }
    assert testbed.farm.simulate_new_staker(at_time, 200) == {
        testbed.reward_asset: 8266
    }
    assert testbed.farm.simulate_new_staker(at_time, 2000) == {
        testbed.reward_asset: 11_808
    }

    # Update farm, estimate should include already accrued rewards.
    testbed.wait_rounds_and_update_farm(4)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 500}
    at_time = testbed.farm.state.updated_at
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 500
    }

    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=1)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 600
    }

    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=10)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 2250
    }

    # Wait until duration is 0
    testbed.wait_rounds_and_update_farm(4)
    assert testbed.farm.state.duration == 1
    assert testbed.farm.state.next_duration == 20

    testbed.wait_rounds_and_update_farm(1)
    assert testbed.farm.state.duration == 20
    assert testbed.farm.state.next_duration == 0

    testbed.wait_rounds_and_update_farm(1)
    assert testbed.farm.state.duration == 19
    assert testbed.farm.state.next_duration == 0

    testbed.wait_rounds_and_update_farm(19)
    assert testbed.farm.state.duration == 0
    assert testbed.farm.state.next_duration == 0

    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=10)
    assert testbed.farm.estimate_accrued_rewards(at_time, user_state) == {
        testbed.reward_asset: 6000
    }

    # Cannot simulate new staker if duration is 0.
    at_time = testbed.farm.state.updated_at + datetime.timedelta(seconds=10)
    assert testbed.farm.simulate_new_staker(at_time, 0) == {testbed.reward_asset: 0}
    assert testbed.farm.simulate_new_staker(at_time, 10) == {testbed.reward_asset: 0}


def test_farming_deposit_next_rewards():
    testbed = make_fresh_farming_testbed()

    # Deposit rewards.
    testbed.deposit_rewards({testbed.reward_asset: 2000}, duration=10)
    assert testbed.farm.state.pending_rewards == {testbed.reward_asset: 2000}
    assert testbed.farm.state.duration == 10
    assert testbed.farm.state.next_rewards == {testbed.reward_asset: 0}
    assert testbed.farm.state.next_duration == 0

    # Deposit next rewards.
    testbed.deposit_rewards({testbed.reward_asset: 50_000}, duration=15)
    assert testbed.farm.state.pending_rewards == {testbed.reward_asset: 2000}
    assert testbed.farm.state.duration == 10
    assert testbed.farm.state.next_rewards == {testbed.reward_asset: 50_000}
    assert testbed.farm.state.next_duration == 15

    # Can't deposit more.
    with pytest.raises(AssertionError) as err:
        testbed.deposit_rewards({testbed.reward_asset: 50_000}, duration=15)
    assert "Cannot deposit next rewards if farm already have next rewards" in str(
        err.value
    )

    # The farm is paused when there are no stakers.
    testbed.wait_rounds_and_update_farm(rounds=5)
    assert testbed.farm.state.duration == 10

    # Stake
    testbed.stake(1000)
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 1000

    # Wait and check rewards.
    testbed.wait_rounds_and_update_farm(rounds=6)
    assert testbed.farm.state.pending_rewards == {testbed.reward_asset: 800}
    assert testbed.farm.state.duration == 4
    assert testbed.farm.state.next_rewards == {testbed.reward_asset: 50_000}
    assert testbed.farm.state.next_duration == 15

    # Wait some more time - the first cycle is finished and the second is started.
    testbed.wait_rounds_and_update_farm(rounds=10)
    assert testbed.farm.state.pending_rewards == {testbed.reward_asset: 30_000}
    assert testbed.farm.state.duration == 9
    assert testbed.farm.state.next_rewards == {testbed.reward_asset: 0}
    assert testbed.farm.state.next_duration == 0

    # Unstake all.
    testbed.unstake(1000)
    assert testbed.staked_asset.get_holding(testbed.escrow.address) == 0

    # Check rewards.
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 25330}

    # Claim rewards.
    with testbed.assert_rewards():
        testbed.claim()

    # The farm is paused again.
    testbed.wait_rounds_and_update_farm(rounds=5)
    assert testbed.farm.state.duration == 8


def test_farming_multiple_reward_assets():
    testbed = make_fresh_farming_testbed()

    # Deposit rewards.
    reward_1 = testbed.reward_asset
    reward_2 = testbed.make_asset("ASA_REW2")
    reward_3 = testbed.make_asset("ASA_REW3")
    rewards = {reward_1: 1000, reward_2: 2000, reward_3: 3000}
    testbed.deposit_rewards(rewards, duration=100)
    assert testbed.farm.state.rewards_per_second == {
        reward_1: 10.0,
        reward_2: 20.0,
        reward_3: 30.0,
    }

    # Stake.
    testbed.stake(100)

    # Wait some rounds.
    testbed.wait_rounds_and_update_farm(10)

    # Check state.
    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=100,
        accrued_rewards={reward_1: 100, reward_2: 200, reward_3: 300},
        claimed_rewards={reward_1: 0, reward_2: 0, reward_3: 0},
        rpt={reward_1: 1.0, reward_2: 2.0, reward_3: 3.0},
    )
    state = testbed.farm.state
    assert state.reward_assets == [reward_1, reward_2, reward_3]
    assert state.distributed_rewards == {reward_1: 100, reward_2: 200, reward_3: 300}
    assert state.claimed_rewards == {reward_1: 0, reward_2: 0, reward_3: 0}
    assert state.pending_rewards == {reward_1: 900, reward_2: 1800, reward_3: 2700}
    assert state.next_rewards == {reward_1: 0, reward_2: 0, reward_3: 0}
    assert state.rpt == {reward_1: 1.0, reward_2: 2.0, reward_3: 3.0}

    # Claim.
    with testbed.assert_rewards():
        testbed.claim()

    # Check state.
    user_state = testbed.escrow.fetch_user_state()
    assert user_state == pactsdk.FarmUserState(
        escrow_id=testbed.escrow.app_id,
        staked=100,
        accrued_rewards={reward_1: 0, reward_2: 0, reward_3: 0},
        claimed_rewards={reward_1: 100, reward_2: 200, reward_3: 300},
        rpt={reward_1: 1.0, reward_2: 2.0, reward_3: 3.0},
    )
    update_farm(testbed.escrow, testbed.user_account)
    state = testbed.farm.state
    assert state.distributed_rewards == {reward_1: 120, reward_2: 240, reward_3: 360}
    assert state.claimed_rewards == {reward_1: 100, reward_2: 200, reward_3: 300}
    assert state.pending_rewards == {reward_1: 880, reward_2: 1760, reward_3: 2640}


def test_farming_rewards_limit():
    def deposit_multiple_rewards(number_of_rewards: int):
        reward_assets = [
            testbed.make_asset(f"ASA_REW{i}") for i in range(number_of_rewards)
        ]
        rewards = {asset: 1000 for asset in reward_assets}
        testbed.deposit_rewards(rewards, duration=100)

    testbed = make_fresh_farming_testbed()

    # Can't put all rewards in a single transaction group. Number of transactions surpasses group size limit. Need to split it into two groups.
    deposit_multiple_rewards(3)
    assert len(testbed.farm.state.reward_assets) == 3
    assert len(testbed.farm.state.pending_rewards) == 3

    # Can't deploy rewards above the limit.
    with pytest.raises(AssertionError) as err:
        deposit_multiple_rewards(5)
    assert "Maximum number of reward assets per farm is 7" in str(err.value)

    # Deploy maximum number of rewards.
    deposit_multiple_rewards(4)
    assert len(testbed.farm.state.reward_assets) == 7
    assert len(testbed.farm.state.pending_rewards) == 7


def test_farming_different_reward_asset_between_cycles():
    testbed = make_fresh_farming_testbed()
    reward_asset_1 = testbed.reward_asset
    reward_asset_2 = testbed.make_asset("ASA_REW2")

    testbed.deposit_rewards({reward_asset_1: 1000}, duration=10)
    testbed.deposit_rewards({reward_asset_2: 2000}, duration=100)

    # Check the state.
    assert testbed.farm.state.pending_rewards == {
        reward_asset_1: 1000,
        reward_asset_2: 0,
    }
    assert testbed.farm.state.duration == 10
    assert testbed.farm.state.next_rewards == {
        reward_asset_1: 0,
        reward_asset_2: 2000,
    }
    assert testbed.farm.state.next_duration == 100

    # Stake.
    testbed.stake(5000)

    # Claim, only the first cycle, one asset is distributed.
    testbed.wait_rounds_and_update_farm(5)
    with testbed.assert_rewards():
        testbed.claim()
    assert reward_asset_1.get_holding(testbed.user_account.address) == 499
    assert reward_asset_2.get_holding(testbed.user_account.address) == 0

    # Claim, cross-cycle, both assets are distributed.
    testbed.wait_rounds_and_update_farm(10)
    with testbed.assert_rewards():
        testbed.claim()
    assert reward_asset_1.get_holding(testbed.user_account.address) == 998
    assert reward_asset_2.get_holding(testbed.user_account.address) == 119

    # Claim, second cycle, only the second asset is distributed.
    testbed.wait_rounds_and_update_farm(10)
    with testbed.assert_rewards():
        testbed.claim()
    assert reward_asset_1.get_holding(testbed.user_account.address) == 998
    assert reward_asset_2.get_holding(testbed.user_account.address) == 338


def test_farming_multiple_stakers():
    testbed = make_fresh_farming_testbed()

    testbed.deposit_rewards({testbed.reward_asset: 150_000}, duration=100)

    account_1, escrow_1 = testbed.user_account, testbed.escrow
    account_2, escrow_2 = make_new_account_and_escrow(
        testbed.farm, testbed.admin_account, [testbed.reward_asset]
    )
    account_3, escrow_3 = make_new_account_and_escrow(
        testbed.farm, testbed.admin_account, [testbed.reward_asset]
    )

    accounts_and_escrows = zip(
        [account_1, account_2, account_3], [escrow_1, escrow_2, escrow_3]
    )

    # Stake all 3 users.
    stake_txs = escrow_1.build_stake_txs(1000)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), account_1)

    stake_txs = escrow_2.build_stake_txs(2000)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), account_2)

    stake_txs = escrow_3.build_stake_txs(3000)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), account_3)

    # Check state.
    wait_rounds(10, account_1)
    update_farm(escrow_1, account_1)
    update_farm(escrow_2, account_2)
    update_farm(escrow_3, account_3)

    assert testbed.farm.state.num_stakers == 3
    assert testbed.farm.state.rpt == {testbed.reward_asset: 5.25}

    user_1_state = escrow_1.fetch_user_state()
    user_2_state = escrow_2.fetch_user_state()
    user_3_state = escrow_3.fetch_user_state()

    assert user_1_state.accrued_rewards == {testbed.reward_asset: 4750}
    assert user_1_state.rpt == {testbed.reward_asset: 4.75}

    assert user_2_state.accrued_rewards == {testbed.reward_asset: 7000}
    assert user_2_state.rpt == {testbed.reward_asset: 5.0}

    assert user_3_state.accrued_rewards == {testbed.reward_asset: 9750}
    assert user_3_state.rpt == {testbed.reward_asset: 5.25}

    for account, escrow in accounts_and_escrows:
        with testbed.assert_rewards(address=account.address):
            claim_tx = escrow.build_claim_rewards_tx()
            sign_and_send(claim_tx, account)

    assert testbed.reward_asset.get_holding(account_1.address) == 4750
    assert testbed.reward_asset.get_holding(account_2.address) == 7000
    assert testbed.reward_asset.get_holding(account_3.address) == 9750

    assert (
        testbed.reward_asset.get_holding(testbed.farm.app_address)
        == 150_000 - 4750 - 7000 - 9750
    )


def test_farming_algo_rewards():
    algo = pactsdk.fetch_asset_by_index(algod, 0)
    testbed = make_fresh_farming_testbed()

    # Deposit algo as rewards.
    testbed.deposit_rewards({algo: 500}, duration=10)
    assert testbed.farm.state.reward_assets == [algo]
    assert testbed.farm.state.pending_rewards == {algo: 500}

    # Stake.
    testbed.stake(1000)

    # Claim.
    testbed.wait_rounds_and_update_farm(3)
    with testbed.assert_rewards():
        testbed.claim()
    update_farm(testbed.escrow, testbed.user_account)
    assert testbed.farm.state.pending_rewards == {algo: 250}

    # Let's mix algo and ASA in the next cycle.
    reward_asset = testbed.make_asset("ASA_REW")
    testbed.deposit_rewards({algo: 1000, reward_asset: 20_000}, duration=10)
    assert testbed.farm.state.reward_assets == [algo, reward_asset]
    assert testbed.farm.state.pending_rewards == {algo: 100, reward_asset: 0}
    assert testbed.farm.state.next_rewards == {algo: 1000, reward_asset: 20_000}

    # Claim.
    testbed.wait_rounds_and_update_farm(5)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {algo: 648, reward_asset: 6_000}
    # old_algo_amount = algo.get_holding(testbed.user_account.address)
    with testbed.assert_rewards():
        testbed.claim()
    update_farm(testbed.escrow, testbed.user_account)
    assert testbed.farm.state.pending_rewards == {algo: 500, reward_asset: 10_000}


def test_farming_stake_for_longer_then_farm_duration():
    testbed = make_fresh_farming_testbed()
    testbed.deposit_rewards({testbed.reward_asset: 1000}, duration=5)
    testbed.stake(100)

    testbed.wait_rounds_and_update_farm(10)
    assert testbed.farm.state.duration == 0
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 1000}
    assert user_state.staked == 100

    # Check if unstake and claim are still working.
    testbed.unstake(100)
    with testbed.assert_rewards():
        testbed.claim()
    assert testbed.reward_asset.get_holding(testbed.user_account.address) == 1000

    # Should be able to stake again but no rewards accruing.
    testbed.stake(100)
    testbed.wait_rounds_and_update_farm(5)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 0}


def test_farming_claim_only_selected_assets():
    testbed = make_fresh_farming_testbed()
    reward_asset_1 = testbed.reward_asset
    reward_asset_2 = testbed.make_asset("ASA_REW2")
    testbed.deposit_rewards({reward_asset_1: 500, reward_asset_2: 1000}, duration=100)
    testbed.stake(1000)

    testbed.wait_rounds_and_update_farm(5)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {reward_asset_1: 24, reward_asset_2: 49}

    # Claim only a single asset.
    claim_tx = testbed.farm.build_claim_rewards_tx(
        testbed.escrow, assets=[reward_asset_2]
    )
    sign_and_send(claim_tx, testbed.user_account)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {reward_asset_1: 24, reward_asset_2: 0}

    # Claim the other asset.
    claim_tx = testbed.farm.build_claim_rewards_tx(
        testbed.escrow, assets=[reward_asset_1]
    )
    sign_and_send(claim_tx, testbed.user_account)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {reward_asset_1: 0, reward_asset_2: 0}


def test_farming_two_users_joining_at_different_time():
    testbed = make_fresh_farming_testbed()
    account_1, escrow_1 = testbed.user_account, testbed.escrow
    account_2, escrow_2 = make_new_account_and_escrow(
        testbed.farm, testbed.admin_account, [testbed.reward_asset]
    )

    testbed.deposit_rewards({testbed.reward_asset: 10_000}, duration=100)

    stake_txs = escrow_1.build_stake_txs(10)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), account_1)

    wait_rounds(10, account_1)
    stake_txs = escrow_2.build_stake_txs(1000)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), account_2)

    wait_rounds(10, account_1)

    update_txs = testbed.farm.build_update_with_opcode_increase_txs(escrow_1)
    sign_and_send(pactsdk.TransactionGroup(update_txs), account_1)

    update_txs = testbed.farm.build_update_with_opcode_increase_txs(escrow_2)
    sign_and_send(pactsdk.TransactionGroup(update_txs), account_2)

    # First user takes all rewards for first 10(+1) seconds and only a little for the next 10.
    user_state_1 = escrow_1.fetch_user_state()
    assert user_state_1.accrued_rewards == {testbed.reward_asset: 1110}

    # Second user takes most rewards for the second 10(+2) seconds.
    user_state_2 = escrow_2.fetch_user_state()
    assert user_state_2.accrued_rewards == {testbed.reward_asset: 1188}


def test_farming_deposit_rewards_with_active_stakers():
    testbed = make_fresh_farming_testbed()

    # First stake.
    testbed.stake(1000)

    # Then add rewards.
    wait_rounds(5, testbed.user_account)
    testbed.deposit_rewards({testbed.reward_asset: 100}, duration=10)

    # Should accrue rewards only for the last round.
    update_farm(testbed.escrow, testbed.user_account)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 9}

    # Should accrue all rewards.
    testbed.wait_rounds_and_update_farm(10)
    wait_rounds(10, testbed.user_account)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 98}
    with testbed.assert_rewards():
        testbed.claim()

    # Deposit more rewards.
    testbed.wait_rounds_and_update_farm(5)
    testbed.deposit_rewards({testbed.reward_asset: 100}, duration=10)

    # Should accrue only the last round.
    update_farm(testbed.escrow, testbed.user_account)
    user_state = testbed.escrow.fetch_user_state()
    assert user_state.accrued_rewards == {testbed.reward_asset: 9}


def test_farming_fetching_assets():
    testbed = make_fresh_farming_testbed()
    testbed.deposit_rewards({testbed.reward_asset: 1000}, duration=100)

    ASSETS_CACHE.clear()

    # Full assets info is not fetched by default to minimize requests to algod.
    farm = testbed.pact.farming.fetch_farm_by_id(testbed.farm.app_id)
    assert farm.staked_asset.unit_name is None
    assert farm.state.reward_assets[0].unit_name is None

    farm.fetch_all_assets()
    assert farm.staked_asset.unit_name == "ASA_STK"
    assert farm.state.reward_assets[0].unit_name == "ASA_REW"


def test_farming_no_testbed():
    # No testbed here so everything is more explicit.
    admin_account = new_account()
    pact = pactsdk.PactClient(algod)

    staked_asset = pact.fetch_asset(create_asset(admin_account, name="ASA_STK"))
    reward_asset = pact.fetch_asset(create_asset(admin_account, name="ASA_REW"))

    # Deploy farm.
    farm_id = deploy_farm(admin_account, staked_asset.index)
    suggested_params = algod.suggested_params()
    farm = pact.farming.fetch_farm_by_id(farm_id)
    farm.set_suggested_params(suggested_params)
    fund_algo_tx = transaction.PaymentTxn(
        sender=admin_account.address,
        receiver=farm.app_address,
        amt=100_000,
        sp=suggested_params,
    )
    sign_and_send(fund_algo_tx, admin_account)

    # Deposit rewards
    deposit_rewards_txs = farm.admin_build_deposit_rewards_txs(
        {reward_asset: 1000}, duration=100
    )
    sign_and_send(pactsdk.TransactionGroup(deposit_rewards_txs), admin_account)

    # Make user account.
    user_account = make_new_account_for_farm(farm, admin_account, [reward_asset])

    # Check that the user doesn't have an escrow.
    escrow = farm.fetch_escrow_by_address(user_account.address)
    assert escrow is None

    # Deploy an escrow.
    deploy_txs = farm.prepare_deploy_escrow_txs(sender=user_account.address)
    sign_and_send(pactsdk.TransactionGroup(deploy_txs), user_account)
    txinfo = algod.pending_transaction_info(deploy_txs[-2].get_txid())
    escrow_id = txinfo["application-index"]
    escrow = farm.fetch_escrow_by_id(escrow_id)
    assert escrow
    escrow.refresh_suggested_params()

    # Stake.
    stake_txs = escrow.build_stake_txs(100)
    sign_and_send(pactsdk.TransactionGroup(stake_txs), user_account)

    # Wait some time.
    wait_rounds(5, user_account)

    # Unstake and claim in a single group.
    unstake_txs = escrow.build_unstake_txs(100)
    claim_tx = escrow.build_claim_rewards_tx()
    group = pactsdk.TransactionGroup([*unstake_txs, claim_tx])
    sign_and_send(group, user_account)

    # Check if the rewards were actually sent.
    assert reward_asset.get_holding(user_account.address) == 59


def test_farming_governance():
    testbed = make_fresh_farming_testbed()
    testbed.deposit_rewards({testbed.reward_asset: 2000}, duration=100)

    testbed.stake(1000)

    testbed.farm.update_state()
    assert testbed.farm.state.total_staked == 1000

    # Commit to governance
    send_message_tx = testbed.escrow.build_send_message_tx(
        testbed.admin_account.address, "some message required by the Foundation"
    )
    sign_and_send(send_message_tx, testbed.user_account)

    # Simulate governance reward.
    transfer_tx = testbed.algo.build_transfer_tx(
        sender=testbed.admin_account.address,
        receiver=testbed.escrow.address,
        amount=100,
        suggested_params=testbed.escrow.suggested_params,
    )
    sign_and_send(transfer_tx, testbed.admin_account)

    escrow_algos = testbed.algo.get_holding(testbed.escrow.address)
    user_algos = testbed.algo.get_holding(testbed.user_account.address)

    # Withdraw reward.
    withdraw_tx = testbed.escrow.build_withdraw_algos()
    sign_and_send(withdraw_tx, testbed.user_account)

    assert testbed.algo.get_holding(testbed.escrow.address) == escrow_algos - 100
    assert (
        testbed.algo.get_holding(testbed.user_account.address)
        == user_algos + 100 - 2000
    )


def test_farming_have_rewards():
    testbed = make_fresh_farming_testbed()
    assert testbed.farm.have_rewards() is False

    testbed.deposit_rewards({testbed.reward_asset: 100}, duration=10)
    assert testbed.farm.have_rewards() is True

    # Farm is freezed.
    dt = testbed.farm.state.updated_at + datetime.timedelta(seconds=20)
    assert testbed.farm.have_rewards(dt) is True

    testbed.stake(10)
    update_farm(testbed.escrow, testbed.user_account)
    dt = testbed.farm.state.updated_at + datetime.timedelta(seconds=5)
    assert testbed.farm.have_rewards(dt) is True

    dt = testbed.farm.state.updated_at + datetime.timedelta(seconds=8)
    assert testbed.farm.have_rewards(dt) is True

    dt = testbed.farm.state.updated_at + datetime.timedelta(seconds=9)
    assert testbed.farm.have_rewards(dt) is False

    dt = testbed.farm.state.updated_at + datetime.timedelta(seconds=20)
    assert testbed.farm.have_rewards(dt) is False

    # Farm is finished.
    testbed.wait_rounds_and_update_farm(10)
    assert testbed.farm.have_rewards() is False
