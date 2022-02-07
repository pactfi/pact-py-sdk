from algosdk.v2client.algod import AlgodClient

from .asset import Asset, fetch_asset_by_index
from .pool import Pool, fetch_pool, list_pools


class PactClient:
    def __init__(self, algod: AlgodClient, pact_api_url="https://api.pact.fi"):
        self.algod = algod
        self.pact_api_url = pact_api_url

    def fetch_asset(self, asset_index: int) -> Asset:
        return fetch_asset_by_index(self.algod, asset_index)

    def list_pools(self, **kwargs) -> dict:
        return list_pools(self.pact_api_url, **kwargs)

    def fetch_pool(
        self,
        primary_asset: Asset,
        secondary_asset: Asset,
        app_id=0,
        fee_bps=30,
    ) -> Pool:
        return fetch_pool(
            algod=self.algod,
            asset_a=primary_asset,
            asset_b=secondary_asset,
            pact_api_url=self.pact_api_url,
            app_id=app_id,
            fee_bps=fee_bps,
        )
