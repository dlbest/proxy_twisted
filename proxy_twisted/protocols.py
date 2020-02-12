#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/12/20 8:51 PM
"""

from twisted.internet.protocol import Protocol
from twisted.internet import error
from twisted.python import failure
import logging


logger = logging.getLogger(__name__)
connectionDone = failure.Failure(error.ConnectionDone())


class ResponseBodyProtocol(Protocol):
    """
    a protocol for response body data
    """

    def __init__(self, deferred):
        self.result = b''
        self.d = deferred

    def dataReceived(self, data):
        self.result += data

    def connectionLost(self, reason=connectionDone):
        self.finished()

    def finished(self):
        self.d.callback(self.result)  # 引用机制的优点：可以让object传送到anywhere if u want
