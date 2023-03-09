from .utils import Account, deploy_contract


def deploy_factory(
    account: Account, contract_type: str, admin_and_treasury_address: str
) -> int:
    command = [
        "deploy-factory",
        f"--contract-type={contract_type.lower()}",
        f"--admin-and-treasury-address={admin_and_treasury_address}",
    ]

    return deploy_contract(account, command)
