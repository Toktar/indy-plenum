import pytest

from plenum.common.log import getlogger
from plenum.common.looper import Looper
from plenum.common.util import get_size
from plenum.test.helper import genTestClient, sendRandomRequests, \
    sendReqsToNodesAndVerifySuffReplies
from plenum.test.node_catchup.helper import \
    ensureClientConnectedToNodesAndPoolLedgerSame
from plenum.test.pool_transactions.helper import buildPoolClientAndWallet


logger = getlogger()


@pytest.yield_fixture(scope="module")
def looper():
    with Looper() as l:
        yield l


def testRequestsSize(looper, txnPoolNodeSet, poolTxnClientNames,
                     tdirWithPoolTxns, poolTxnData):
    """
    Client should not be using node registry but pool transaction file
    :return:
    """
    clients = []
    for name in poolTxnClientNames:
        seed = poolTxnData["seeds"][name].encode()
        client, wallet = buildPoolClientAndWallet((name, seed),
                                                  tdirWithPoolTxns)
        looper.add(client)
        ensureClientConnectedToNodesAndPoolLedgerSame(looper, client,
                                                      *txnPoolNodeSet)
        clients.append((client, wallet))

    n = 50
    for (client, wallet) in clients:
        logger.debug("{} sending {} requests".format(client, n))
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client, n, 1, 5)
    for node in txnPoolNodeSet:
        logger.debug("{} has requests {} with size {}".
                     format(node, len(node.requests), get_size(node.requests)))
