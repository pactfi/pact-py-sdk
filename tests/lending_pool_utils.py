import base64
import functools
import pathlib
from dataclasses import dataclass

import algosdk

import pactsdk
from pactsdk.utils import get_last_round, sp_fee

from .pool_utils import deploy_exchange
from .utils import (
    ROOT_ACCOUNT,
    Account,
    algod,
    create_asset,
    deploy_contract,
    new_account,
    sign_and_send,
    wait_rounds,
)


def get_program(teal_path: str) -> str:
    with open(pathlib.Path.cwd() / teal_path) as f:
        return f.read()


@functools.cache
def get_compiled_program(teal_path: str) -> bytes:
    program = get_program(teal_path)
    compiled = algod.compile(program)["result"]
    return base64.b64decode(compiled)


def deploy_folks_manager():
    sp = algod.suggested_params()

    create_tx = algosdk.transaction.ApplicationCreateTxn(
        sender=ROOT_ACCOUNT.address,
        sp=sp_fee(sp, 2000),
        on_complete=algosdk.transaction.OnComplete.NoOpOC,
        approval_program=get_compiled_program("contract-mocks/build/empty.teal"),
        clear_program=get_compiled_program("contract-mocks/build/empty.teal"),
        global_schema=algosdk.transaction.StateSchema(0, 0),
        local_schema=algosdk.transaction.StateSchema(0, 0),
    )

    txid = sign_and_send(create_tx, ROOT_ACCOUNT)
    return algod.pending_transaction_info(txid)["application-index"]


def deploy_folks_lending_pool(
    original_asset_id: int,
    manager_id: int,
    interest_rate: int,
    interest_index: int,
    updated_at: int,
):
    sp = algod.suggested_params()

    create_tx = algosdk.transaction.ApplicationCreateTxn(
        sender=ROOT_ACCOUNT.address,
        sp=sp_fee(sp, 1000),
        on_complete=algosdk.transaction.OnComplete.NoOpOC,
        approval_program=get_compiled_program(
            "contract-mocks/build/folks_lending_pool_mock.teal"
        ),
        clear_program=get_compiled_program("contract-mocks/build/empty.teal"),
        global_schema=algosdk.transaction.StateSchema(1, 3),
        local_schema=algosdk.transaction.StateSchema(0, 0),
        extra_pages=0,
    )
    txid = sign_and_send(create_tx, ROOT_ACCOUNT)
    app_id = algod.pending_transaction_info(txid)["application-index"]

    # Fund the contract.
    fund_tx = algosdk.transaction.PaymentTxn(
        sender=ROOT_ACCOUNT.address,
        amt=300_000,
        receiver=algosdk.logic.get_application_address(app_id),
        sp=sp,
    )

    # Init the app.
    init_tx = algosdk.transaction.ApplicationNoOpTxn(
        sender=ROOT_ACCOUNT.address,
        sp=sp_fee(sp, 3000),
        index=app_id,
        app_args=["init", manager_id, interest_rate, interest_index, updated_at],
        foreign_assets=[original_asset_id] if original_asset_id else [],
    )

    group = pactsdk.TransactionGroup([fund_tx, init_tx])
    sign_and_send(group, ROOT_ACCOUNT)

    return app_id


def deploy_lending_pool_adapter():
    return deploy_contract(ROOT_ACCOUNT, ["lending-pool-adapter"])


@dataclass
class LendingPoolAdapterTestBed:
    __test__ = False

    account: Account
    pact: pactsdk.PactClient
    algo: pactsdk.Asset
    original_asset: pactsdk.Asset
    lending_pool_adapter: pactsdk.FolksLendingPoolAdapter

    def add_liquidity(
        self, primary_asset_amount: int, secondary_asset_amount: int, slippage_pct=0.0
    ):
        lending_liquidity_addition = self.lending_pool_adapter.prepare_add_liquidity(
            primary_asset_amount, secondary_asset_amount, slippage_pct
        )
        tx_group = self.lending_pool_adapter.prepare_add_liquidity_tx_group(
            self.account.address, lending_liquidity_addition
        )
        sign_and_send(tx_group, self.account)
        self.lending_pool_adapter.pact_pool.update_state()


def make_fresh_lending_pool_testbed() -> LendingPoolAdapterTestBed:
    user = new_account()

    original_asset_id = create_asset(account=user, name="USDC Coin", unit_name="USDC")

    manager_id = deploy_folks_manager()

    wait_rounds(10, user)
    updated_at = get_last_round(algod) - 10

    # Simulates Folks mainnet Algo pool (147169673).
    primary_lending_pool_id = deploy_folks_lending_pool(
        original_asset_id=0,
        manager_id=manager_id,
        interest_index=103440176304992,
        interest_rate=6229129240500989,
        updated_at=updated_at,
    )

    # Simulates Folks mainnet USDC pool (147170678).
    secondary_lending_pool_id = deploy_folks_lending_pool(
        original_asset_id=original_asset_id,
        manager_id=manager_id,
        interest_index=100278968447135,
        interest_rate=44080950253372,
        updated_at=updated_at,
    )

    lending_pool_adapter_id = deploy_lending_pool_adapter()

    pact = pactsdk.PactClient(
        algod, folks_lending_pool_adapter_id=lending_pool_adapter_id
    )

    primary_lending_pool = pact.fetch_folks_lending_pool(primary_lending_pool_id)
    secondary_lending_pool = pact.fetch_folks_lending_pool(secondary_lending_pool_id)

    pact_pool_id = deploy_exchange(
        account=user,
        pool_type="CONSTANT_PRODUCT",
        primary_asset_index=primary_lending_pool.f_asset.index,
        secondary_asset_index=secondary_lending_pool.f_asset.index,
    )
    pact_pool = pact.fetch_pool_by_id(pact_pool_id)

    lending_pool_adapter = pact.get_folks_lending_pool_adapter(
        pact_pool=pact_pool,
        primary_lending_pool=primary_lending_pool,
        secondary_lending_pool=secondary_lending_pool,
    )

    # Opt in adapter to assets.
    asset_ids = [
        primary_lending_pool.original_asset.index,
        secondary_lending_pool.original_asset.index,
        primary_lending_pool.f_asset.index,
        secondary_lending_pool.f_asset.index,
        pact_pool.liquidity_asset.index,
    ]
    tx_group = lending_pool_adapter.prepare_opt_in_to_asset_tx_group(
        user.address, asset_ids
    )
    sign_and_send(tx_group, user)

    # Opt in user to LP token.
    opt_in_tx = pact_pool.liquidity_asset.prepare_opt_in_tx(user.address)
    sign_and_send(opt_in_tx, user)

    last_round = get_last_round(algod)
    primary_lending_pool.last_timestamp_override = last_round
    secondary_lending_pool.last_timestamp_override = last_round

    return LendingPoolAdapterTestBed(
        account=user,
        pact=pact,
        algo=pact.fetch_asset(0),
        original_asset=pact.fetch_asset(original_asset_id),
        lending_pool_adapter=lending_pool_adapter,
    )
