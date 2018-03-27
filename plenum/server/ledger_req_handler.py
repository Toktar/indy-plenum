from typing import List

import base58

from plenum.common.ledger import Ledger
from plenum.common.request import Request
from plenum.persistence.util import txnsWithSeqNo
from plenum.server.req_handler import RequestHandler
from stp_core.common.log import getlogger

from state.state import State

logger = getlogger()


class LedgerRequestHandler(RequestHandler):
    """
    Base class for request handlers
    Declares methods for validation, application of requests and
    state control
    """

    def __init__(self, ledger: Ledger, state: State):
        self.state = state
        self.ledger = ledger

    def updateState(self, txns, isCommitted=False):
        """
        Updates current state with a number of committed or
        not committed transactions
        """

    def commit(self, txnCount, stateRoot, txnRoot, ppTime) -> List:
        """
        :param txnCount: The number of requests to commit (The actual requests
        are picked up from the uncommitted list from the ledger)
        :param stateRoot: The state trie root after the txns are committed
        :param txnRoot: The txn merkle root after the txns are committed

        :return: list of committed transactions
        """

        (seqNoStart, seqNoEnd), committedTxns = \
            self.ledger.commitTxns(txnCount)
        stateRoot = base58.b58decode(stateRoot.encode())
        # Probably the following assertion fail should trigger catchup
        assert self.ledger.root_hash == txnRoot, '{} {}'.format(
            self.ledger.root_hash, txnRoot)
        self.state.commit(rootHash=stateRoot)
        return txnsWithSeqNo(seqNoStart, seqNoEnd, committedTxns)

    def onBatchCreated(self, state_root):
        pass

    def onBatchRejected(self):
        pass

    def is_query(self, txn_type):
        return txn_type in self.query_types

    def get_query_response(self, request):
        raise NotImplementedError

    @staticmethod
    def transform_txn_for_ledger(txn):
        return txn

