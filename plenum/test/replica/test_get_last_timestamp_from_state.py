from plenum.common.config_helper import PNodeConfigHelper
from plenum.common.constants import DOMAIN_LEDGER_ID
from plenum.common.util import get_utc_epoch
from plenum.test.helper import sdk_send_random_and_check
from plenum.test.node_catchup.helper import waitNodeDataEquality
from plenum.test.pool_transactions.helper import disconnect_node_and_ensure_disconnected, \
    reconnect_node_and_ensure_connected
from plenum.test.test_node import get_master_primary_node, TestNode, \
    checkNodesConnected
from stp_core.types import HA


def test_get_last_ordered_timestamp_after_catchup(looper,
                                                  txnPoolNodeSet,
                                                  sdk_pool_handle,
                                                  sdk_wallet_steward,
                                                  tconf,
                                                  tdir,
                                                  allPluginsPath):
    node_to_disconnect = txnPoolNodeSet[-1]
    reply_before = sdk_send_random_and_check(looper,
                                             txnPoolNodeSet,
                                             sdk_pool_handle,
                                             sdk_wallet_steward,
                                             1)[0][1]
    looper.runFor(2)
    disconnect_node_and_ensure_disconnected(looper,
                                            txnPoolNodeSet,
                                            node_to_disconnect)
    looper.removeProdable(name=node_to_disconnect.name)
    reply = sdk_send_random_and_check(looper,
                                      txnPoolNodeSet,
                                      sdk_pool_handle,
                                      sdk_wallet_steward,
                                      1)[0][1]

    nodeHa, nodeCHa = HA(*node_to_disconnect.nodestack.ha), HA(
        *node_to_disconnect.clientstack.ha)
    config_helper = PNodeConfigHelper(node_to_disconnect.name, tconf, chroot=tdir)
    node_to_disconnect = TestNode(
        node_to_disconnect.name,
        config_helper=config_helper,
        config=tconf,
        ha=nodeHa,
        cliha=nodeCHa,
        pluginPaths=allPluginsPath)
    looper.add(node_to_disconnect)
    txnPoolNodeSet[-1] = node_to_disconnect
    looper.run(checkNodesConnected(txnPoolNodeSet))
    waitNodeDataEquality(looper, node_to_disconnect, *txnPoolNodeSet[:-1])
    ts_from_state = node_to_disconnect.master_replica._get_last_timestamp_from_state(DOMAIN_LEDGER_ID)
    assert ts_from_state == reply['result']['txnTime']
    assert ts_from_state != reply_before['result']['txnTime']


def test_choose_ts_from_state(looper,
                              txnPoolNodeSet,
                              sdk_pool_handle,
                              sdk_wallet_steward):
    sdk_send_random_and_check(looper,
                              txnPoolNodeSet,
                              sdk_pool_handle,
                              sdk_wallet_steward,
                              1)
    primary_node = get_master_primary_node(txnPoolNodeSet)
    excpected_ts = get_utc_epoch() + 30
    req_handler = primary_node.getDomainReqHandler()
    req_handler.ts_store.set(excpected_ts,
                                  req_handler.state.headHash)
    primary_node.master_replica.last_accepted_pre_prepare_time = None
    reply = sdk_send_random_and_check(looper,
                                      txnPoolNodeSet,
                                      sdk_pool_handle,
                                      sdk_wallet_steward,
                                      1)[0][1]
    assert abs(excpected_ts - int(reply['result']['txnTime'])) < 3




