import pytest

from tests.utils import make_fresh_testbed


@pytest.fixture
def testbed():
    return make_fresh_testbed()
