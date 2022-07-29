import pytest
from freezegun import freeze_time

from tests.utils import make_fresh_testbed


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
