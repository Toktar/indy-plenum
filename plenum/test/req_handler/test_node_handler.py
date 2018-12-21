import pytest as pytest

from plenum.common.constants import ROLE, NYM, TARGET_NYM, TXN_TYPE, DOMAIN_LEDGER_ID, NODE, STEWARD, NODE_IP, \
    NODE_PORT, CLIENT_IP, CLIENT_PORT, ALIAS, DATA
from plenum.common.exceptions import UnauthorizedClientRequest
from plenum.common.request import Request
from plenum.common.txn_util import get_payload_data, reqToTxn, get_reply_nym
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.node_handler import NodeHandler
from plenum.test.req_handler.helper import create_nym_txn, get_state
from plenum.test.testing_utils import FakeSomething
from state.state import State


@pytest.fixture(scope="function")
def node_handler(tconf, nym_handler):
    data_manager = DatabaseManager()
    handler = NodeHandler(tconf, data_manager, FakeSomething())
    data_manager.register_new_database(handler.ledger_id,
                                       FakeSomething(),
                                       get_state())
    nym_db = nym_handler.database_manager.get_database(nym_handler.ledger_id)
    data_manager.register_new_database(nym_handler.ledger_id,
                                       nym_db.ledger,
                                       nym_db.state)
    return handler


def test_dynamic_validation_update(node_handler, nym_handler):
    identifier = "test_identifier"
    nym_handler.updateNym(identifier, create_nym_txn(identifier, STEWARD))
    node_handler.updateState([_create_node_txn(identifier)])
    request = _create_node_request(identifier, node_port="789")
    node_handler.dynamic_validation(request)


def test_dynamic_validation_update_by_not_steward(node_handler, nym_handler):
    identifier = "test_identifier"
    nym_handler.updateNym(identifier, create_nym_txn(identifier, ""))
    node_handler.updateState([_create_node_txn(identifier)])
    request = _create_node_request(identifier, node_port="789")
    node_handler.dynamic_validation(request)


def test_dynamic_validation_add_by_not_steward(node_handler, nym_handler):
    identifier = "test_identifier"
    nym_handler.updateNym(identifier, create_nym_txn(identifier, ""))
    request = _create_node_request(identifier, node_port="789")
    node_handler.dynamic_validation(request)


def test_dynamic_validation_add(node_handler, nym_handler):
    identifier = "test_identifier"
    nym_handler.updateNym(identifier, create_nym_txn(identifier, STEWARD))
    request = _create_node_request(identifier)
    node_handler.dynamic_validation(request)


def test_dynamic_validation_update_with_request_duplicate(node_handler, nym_handler):
    identifier = "test_identifier"
    nym_handler.updateNym(identifier, create_nym_txn(identifier, STEWARD))
    node_handler.updateState([_create_node_txn(identifier)])
    request = _create_node_request(identifier)
    with pytest.raises(UnauthorizedClientRequest) as e:
        node_handler.dynamic_validation(request)
    assert "node already has the same data as requested" \
           in e._excinfo[1].args[0]


def test_dynamic_validation_msg_from_not_steward(node_handler):
    identifier = "test_identifier"
    node_handler.updateNym(identifier, _create_node_txn(identifier, ""))
    request = Request(identifier=identifier,
                      operation={ROLE: ""})

    with pytest.raises(UnauthorizedClientRequest) as e:
        node_handler.dynamic_validation(request)
    assert "Only Steward is allowed to do these transactions" \
           in e._excinfo[1].args[0]

#
# def test_dynamic_validation_steward_create_steward_before_limit(node_handler):
#     identifier = "test_identifier"
#     node_handler.updateNym(identifier, _create_node_txn(identifier))
#     request = Request(identifier=identifier,
#                       operation={ROLE: STEWARD})
#     node_handler.dynamic_validation(request)
#
#
# def test_dynamic_validation_steward_create_steward_after_limit(node_handler):
#     identifier = "test_identifier"
#     node_handler.updateNym(identifier, _create_node_txn(identifier))
#     old_steward_threshold = node_handler.config.stewardThreshold
#     node_handler.config.stewardThreshold = 1
#
#     request = Request(identifier=identifier,
#                       operation={ROLE: STEWARD})
#
#     with pytest.raises(UnauthorizedClientRequest) as e:
#         node_handler.dynamic_validation(request)
#     assert "New stewards cannot be added by other stewards as there are already" \
#            in e._excinfo[1].args[0]
#
#     node_handler.config.stewardThreshold = old_steward_threshold
#
#
# def test_update_state(node_handler):
#     txns = []
#     for i in range(5):
#         txns.append(_create_node_txn("identifier{}".format(i), str(i)))
#     node_handler.updateState(txns)
#
#     for txn in txns:
#         nym_data = node_handler.getNymDetails(node_handler.state, get_reply_nym(txn))
#         assert nym_data[ROLE] == STEWARD
#
#
# def test_update_nym(node_handler):
#     identifier = "identifier"
#     txn1 = _create_node_txn(identifier)
#     txn2 = _create_node_txn(identifier, "")
#
#     node_handler.updateNym(identifier, txn1)
#     nym_data = node_handler.getNymDetails(node_handler.state, identifier)
#     assert get_payload_data(txn1)[ROLE] == nym_data[ROLE]
#
#     node_handler.updateNym(identifier, txn2)
#     nym_data = node_handler.getNymDetails(node_handler.state, identifier)
#     assert get_payload_data(txn2)[ROLE] == nym_data[ROLE]
#
#
# def test_get_role(node_handler):
#     identifier = "test_identifier"
#     node_handler.updateNym(identifier, _create_node_txn(identifier))
#     nym_data = node_handler.get_role(node_handler.state, identifier)
#     assert nym_data[ROLE] == STEWARD
#
#
# def test_get_role_nym_without_role(node_handler):
#     identifier = "test_identifier"
#     node_handler.updateNym(identifier, _create_node_txn(identifier, ""))
#     nym_data = node_handler.get_role(node_handler.state, identifier)
#     assert not nym_data
#
#
# def test_get_role_without_nym_data(node_handler):
#     identifier = "test_identifier"
#     nym_data = node_handler.get_role(node_handler.state, identifier)
#     assert not nym_data
#
#
# def test_is_steward(node_handler):
#     identifier = "test_identifier"
#     node_handler.updateNym(identifier, _create_node_txn(identifier))
#     assert node_handler.isSteward(node_handler.state, identifier)
#     assert not node_handler.isSteward(node_handler.state, "other_identifier")
#

def _create_node_txn(identifier, nym="TARGET_NYM", alias="test_node"):
    return reqToTxn(_create_node_request(identifier, nym, alias))


def _create_node_request(identifier, nym="TARGET_NYM", alias="test_node", node_port="123"):
    return Request(identifier=identifier,
                   operation={TXN_TYPE: NODE,
                              TARGET_NYM: nym,
                              DATA: {
                                  ALIAS: alias,
                                  NODE_IP: "0.0.0.1",
                                  NODE_PORT: node_port,
                                  CLIENT_IP: "0.0.0.1",
                                  CLIENT_PORT: "321"
                              }
                              })
