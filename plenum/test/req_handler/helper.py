from plenum.common.config_helper import PNodeConfigHelper
from plenum.common.constants import ROLE, TXN_TYPE, NYM, TARGET_NYM
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn
from plenum.test.test_node import ensure_node_disconnected, checkNodesConnected, ensureElectionsDone, TestNode
from state.state import State


def create_nym_txn(identifier, role, nym="TARGET_NYM"):
    return reqToTxn(Request(identifier=identifier,
                            operation={ROLE: role,
                                       TXN_TYPE: NYM,
                                       TARGET_NYM: nym}))


def get_state():
    state = State()
    state.txn_list = {}
    state.get = lambda key, isCommitted: state.txn_list.get(key, None)
    state.set = lambda key, value: state.txn_list.update({key: value})
    state.as_dict = state.txn_list
    return state
