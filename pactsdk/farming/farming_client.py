from typing import Optional

from algosdk.v2client.algod import AlgodClient

from .escrow import Escrow, fetch_escrow_by_id, list_escrows_from_account_info
from .farm import Farm, fetch_farm_by_id


class PactFarmingClient:
    """An entry point for interacting with the farming SDK."""

    algod: AlgodClient
    """Algorand client to work with."""

    def __init__(self, algod: AlgodClient):
        """
        Args:
            algod: Algorand client to work with.
        """
        self.algod = algod

    def fetch_farm_by_id(self, app_id: int) -> Farm:
        return fetch_farm_by_id(algod=self.algod, app_id=app_id)

    def fetch_escrow_by_id(self, app_id: int) -> Escrow:
        return fetch_escrow_by_id(algod=self.algod, app_id=app_id)

    def list_escrows(
        self, user_address: str, farms: Optional[list[Farm]] = None
    ) -> list[Escrow]:
        account_info = self.algod.account_info(user_address)
        return self.list_escrows_from_account_info(account_info, farms)

    def list_escrows_from_account_info(
        self, account_info: dict, farms: Optional[list[Farm]] = None
    ) -> list[Escrow]:
        return list_escrows_from_account_info(self.algod, account_info, farms)
