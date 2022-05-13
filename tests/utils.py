import os
import re
import subprocess
from dataclasses import dataclass
from typing import Literal, Optional, Union

import algosdk
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

import pactsdk


@dataclass
class Account:
    address: str
    private_key: str

    @staticmethod
    def from_mnemonic(mnemonic: str):
        private_key = algosdk.mnemonic.to_private_key(mnemonic)
        return Account(
            address=algosdk.account.address_from_private_key(private_key),
            private_key=private_key,
        )


ROOT_ACCOUNT = Account.from_mnemonic(
    "jelly swear alcohol hybrid wrong camp prize attack hurdle shaft solar entry inner arm region economy awful inch they squirrel sort renew legend absorb giant"
)

algod = AlgodClient(
    "8cec5f4261a2b5ad831a8a701560892cabfe1f0ca00a22a37dee3e1266d726e3",
    "http://localhost:8787",
)


def sign_and_send(
    tx_to_send: Union[transaction.Transaction, pactsdk.TransactionGroup],
    account: Account,
):
    signed_tx = tx_to_send.sign(account.private_key)
    if type(tx_to_send) == pactsdk.TransactionGroup:
        txid = algod.send_transactions(signed_tx)
    else:
        txid = algod.send_transaction(signed_tx)
    return txid


def create_asset(
    account: Account,
    name: Optional[str] = "COIN",
    decimals=6,
    total=1_000_000,
) -> int:
    suggested_params = algod.suggested_params()

    txn = transaction.AssetCreateTxn(
        sender=account.address,
        sp=suggested_params,
        total=total,
        decimals=decimals,
        default_frozen=0,
        unit_name=name,
        asset_name=name,
    )

    sign_and_send(txn, account)
    ptx = algod.pending_transaction_info(txn.get_txid())
    return ptx["asset-index"]


PoolType = Literal["CONSTANT_PRODUCT", "STABLESWAP"]


def deploy_contract(
    account: Account,
    pool_type: PoolType,
    primary_asset_index: int,
    secondary_asset_index: int,
    fee_bps=30,
    pact_fee_bps=30,
    amplifier=80,
) -> int:
    mnemonic = algosdk.mnemonic.from_private_key(account.private_key)

    command = [
        "poetry",
        "run",
        "python",
        "scripts/deploy.py",
        f"--contract-type={pool_type.lower()}",
        f"--primary_asset_id={primary_asset_index}",
        f"--secondary_asset_id={secondary_asset_index}",
        f"--fee_bps={fee_bps}",
        f"--pact_fee_bps={pact_fee_bps}",
        f"--amplifier={amplifier}",
        f"--admin_and_treasury_address={account.address}",
    ]

    env = {
        "PATH": os.environ["PATH"],
        "ALGOD_URL": "http://localhost:8787",
        "ALGOD_TOKEN": "8cec5f4261a2b5ad831a8a701560892cabfe1f0ca00a22a37dee3e1266d726e3",
        "DEPLOYER_MNEMONIC": mnemonic,
    }

    process = subprocess.run(
        command, cwd="algorand-testbed", env=env, capture_output=True
    )
    if process.stderr:
        raise RuntimeError(f"Failed to deploy contract: {process.stderr.decode()}")

    match = re.search(r"EC ID: (\d+)", process.stdout.decode())
    if not match:
        raise RuntimeError("Can't find app id in std out.")

    return int(match[1])


def add_liqudity(
    account: Account,
    pool: pactsdk.Pool,
    primary_asset_amount=10_000,
    secondary_asset_amount=10_000,
):
    opt_in_tx = pool.liquidity_asset.prepare_opt_in_tx(account.address)
    sign_and_send(opt_in_tx, account)

    add_liq_tx_group = pool.prepare_add_liquidity_tx_group(
        address=account.address,
        primary_asset_amount=primary_asset_amount,
        secondary_asset_amount=secondary_asset_amount,
    )
    sign_and_send(add_liq_tx_group, account)
    pool.update_state()


def new_account():
    # Accounts has a limit of 10 apps and 100 assets. Therefore, we need to create a new account for most of the tests.
    private_key, address = algosdk.account.generate_account()
    account = Account(address=address, private_key=private_key)
    fund_account_with_algos(account, 10_000_000)
    return account


def fund_account_with_algos(
    account: Account,
    amount: int,
):
    suggested_params = algod.suggested_params()
    tx = transaction.PaymentTxn(
        sender=ROOT_ACCOUNT.address,
        receiver=account.address,
        amt=amount,
        sp=suggested_params,
    )
    sign_and_send(tx, ROOT_ACCOUNT)


@dataclass
class TestBed:
    __test__ = False

    account: Account
    pact: pactsdk.PactClient
    algo: pactsdk.Asset
    coin: pactsdk.Asset
    pool: pactsdk.Pool


def make_fresh_testbed(fee_bps=30) -> TestBed:
    account = new_account()
    pact = pactsdk.PactClient(algod)

    coin_index = create_asset(account)

    app_id = deploy_contract(
        pool_type="CONSTANT_PRODUCT",
        account=account,
        primary_asset_index=0,
        secondary_asset_index=coin_index,
        fee_bps=fee_bps,
    )
    pool = pact.fetch_pool_by_id(app_id=app_id)

    return TestBed(
        account=account,
        pact=pact,
        algo=pool.primary_asset,
        coin=pool.secondary_asset,
        pool=pool,
    )
