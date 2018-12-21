import pytest

from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.nym_handler import NymHandler
from plenum.test.req_handler.helper import get_state
from plenum.test.testing_utils import FakeSomething


@pytest.fixture(scope="function")
def nym_handler(tconf):
    data_manager = DatabaseManager()
    handler = NymHandler(tconf, data_manager)
    data_manager.register_new_database(handler.ledger_id,
                                       FakeSomething(),
                                       get_state())
    return handler