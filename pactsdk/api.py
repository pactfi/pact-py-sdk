"""Module for interacting with Pact API."""

from typing import TypedDict
from urllib.parse import urlencode

import requests


class ListPoolsParams(TypedDict, total=False):
    """Parameters for calling the :py:func:`pactsdk.pool.list_pools` function.

    All keys are optional and can be omitted.
    """

    offset: int
    limit: int
    is_verified: str
    creator: str
    primary_asset__on_chain_id: int
    secondary_asset__on_chain_id: int
    primary_asset__unit_name: str
    secondary_asset__unit_name: str
    primary_asset__name: str
    secondary_asset__name: str


class ApiAsset(TypedDict):
    """Details about the liquidity pool assets returned from the asset pool."""

    on_chain_id: str
    decimals: int
    id: int
    is_liquidity_token: bool
    is_verified: bool
    name: str
    total_amount: str
    tvl_usd: str
    unit_name: str
    volume_7d: str
    volume_24h: str


class ApiPool(TypedDict):
    """The individual pool information returned from :py:func:`pactsdk.pool.list_pools`, this contains the basic pool information."""

    address: str
    on_chain_id: str
    confirmed_round: int
    creator: str
    fee_amount_7d: str
    fee_amount_24h: str
    fee_usd_7d: str
    fee_usd_24h: str
    tvl_usd: str
    volume_7d: str
    volume_24h: str
    apr_7d: str
    id: int
    is_verified: bool
    pool_asset: ApiAsset
    primary_asset: ApiAsset
    secondary_asset: ApiAsset


class ApiListPoolsResponse(TypedDict):
    """Response from :py:func:`pactsdk.pool.list_pools` function containing pagination information and results."""

    count: int
    offset: int
    limit: int
    results: list[ApiPool]


def list_pools(pact_api_url: str, params: ListPoolsParams) -> ApiListPoolsResponse:
    """Finds all the pools that match the pool options passed in.

    Args:
        pact_api_url: The API URL to query the list of pools.
        params: Dict of params for querying the pools.

    Returns:
        Pool data for all pools in the Pact that meets the pool options.
    """
    assert pact_api_url
    encoded_params = urlencode(params)
    response = requests.get(f"{pact_api_url}/api/pools?{encoded_params}")
    return response.json()
