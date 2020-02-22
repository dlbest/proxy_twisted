#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 12/30/19 8:19 PM
"""


from RPC_twisted.server import BaseServer, DistributedServer

from RPC_twisted.client import BaseClient, DistributedClient


import logging

logger = logging.getLogger(__name__)


class ServerBuilder(object):
    """
    server factory class for one kind of service
    """
    server = DistributedServer

    def __init__(self, interface, interface_impl):
        self.interface = interface
        self.interface_impl = interface_impl

    def build(self, host, port):
        s = self.server(host, port, self.interface, self.interface_impl)
        return s



