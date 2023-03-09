from algosdk.v2client.algod import AlgodClient

from ..config import Config
from .escrow import Escrow, fetch_escrow_by_id
from .farm import Farm, fetch_farm_by_id


class PactFarmingClient:
    """An entry point for interacting with the farming SDK."""

    algod: AlgodClient
    """Algorand client to work with."""

    config: Config

    def __init__(self, algod: AlgodClient, config: Config):
        """
        Args:
            algod: Algorand client to work with.
        """
        self.algod = algod
        self.config = config

    def fetch_farm_by_id(self, app_id: int) -> Farm:
        return fetch_farm_by_id(algod=self.algod, app_id=app_id)

    def fetch_escrow_by_id(self, app_id: int) -> Escrow:
        return fetch_escrow_by_id(algod=self.algod, app_id=app_id)
