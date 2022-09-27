import pytest
from freezegun import freeze_time

import pactsdk
from tests.pool_utils import make_fresh_testbed

from .utils import deploy_gas_station


@pytest.fixture
def testbed():
    return make_fresh_testbed("CONSTANT_PRODUCT")


@pytest.fixture
def testbed_v_1():
    return make_fresh_testbed("CONSTANT_PRODUCT", version=1)


@pytest.fixture()
def time():
    with freeze_time("2021-06-01") as ft:
        yield ft


@pytest.fixture(scope="session")
def gas_station():
    gas_station_app_id = deploy_gas_station()
    pactsdk.set_gas_station(gas_station_app_id)
