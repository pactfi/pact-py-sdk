import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, Union

import algosdk
from algosdk import transaction
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
    total=100_000_000,
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


def new_account():
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


def deploy_contract(account: Account, command: list[str]):
    mnemonic = algosdk.mnemonic.from_private_key(account.private_key)

    command = ["poetry", "run", "python", "scripts/deploy.py", *command]
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

    match = re.search(r"APP ID: (\d+)", process.stdout.decode())
    if not match:
        raise RuntimeError("Can't find app id in std out.")

    return int(match[1])


def deploy_gas_station():
    gas_station_id = deploy_contract(ROOT_ACCOUNT, ["gas-station"])

    suggested_params = algod.suggested_params()
    tx = transaction.PaymentTxn(
        sender=ROOT_ACCOUNT.address,
        receiver=algosdk.logic.get_application_address(gas_station_id),
        amt=100_000,
        sp=suggested_params,
    )
    sign_and_send(tx, ROOT_ACCOUNT)

    return gas_station_id


def wait_rounds(rounds: int, account: Account):
    suggested_params = algod.suggested_params()
    for i in range(rounds):
        tx = transaction.PaymentTxn(
            sender=account.address,
            receiver=account.address,
            amt=0,
            sp=suggested_params,
            note=bytes(i),
        )
        sign_and_send(tx, account)


def get_last_block():
    status_data = algod.status()
    return status_data["last-round"]
