#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 2/13/20 5:00 PM
"""


from abc import ABC

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.python import failure
from twisted.internet import error

import socket
import json
import weakref
import logging

from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

connectionDone = failure.Failure(error.ConnectionDone())


class BaseConnection(metaclass=ABCMeta):

    @abstractmethod
    def read(self, *args, **kwargs):
        pass

    @abstractmethod
    def write(self, *args, **kwargs):
        pass


# server endpoint

class RPCProtocol(LineReceiver, ABC):
    """
    RPC protocol class, raw data processor
    this protocol is bound to transport(connection) class from twisted
    """
    conn_counts = 0       # protocols class need a cash to save the connection amount to which any instance have access

    def __init__(self, interface, impl, hcls, *args, **kwargs):       # a protocol instance for a connection
        self.handler = hcls(self, interface, impl, *args, **kwargs)   # instantiate a handler

    def lineReceived(self, line):                    # command line
        try:
            line = line.decode('utf-8')
            line = json.loads(line)                  # deserialization
            logger.debug(line)
            result = self.handler(line)
        except Exception as e:
            result = 'error: %s' % str(e)
        finally:
            result = json.dumps(result)
            logger.debug(result)
            self.sendLine(result.encode('utf-8'))

    def connectionMade(self):
        logger.info('connection with ' + str(self.transport.client) + ' is successful!')
        server = self.factory().server()
        self.conn_counts += 1
        res = server.update_conn_counts(self.conn_counts, str(self.transport.client))
        if not res:
            self.sendLine(b'connection pool is full, rejected!')
            self.transport.loseConnection()
        del server

    def connectionLost(self, reason=connectionDone):   # will get b'' continuously when connection lost
        logger.debug('connection with ' + str(self.transport.client) + 'is closed!')
        self.conn_counts -= 1
        server = self.factory().server()
        res = server.update_conn_counts(self.conn_counts, str(self.transport.client))
        del server


class RPCFactory(Factory):

    protocol = RPCProtocol

    def __init__(self, interface, impl, hcls):
        self.interface = interface
        self.hcls = hcls
        self.impl = impl

    def buildProtocol(self, addr):
        p = self.protocol(self.interface, self.impl, self.hcls)
        p.factory = weakref.ref(self)
        return p

#######################################################################################################################
# client endpoint


class ClientTransport(BaseConnection):

    """
    this class wraps a connection for a client endpoint, so it is one layer of application protocols layer by itself
    its upper protocol layers in dynamicProxy

    """

    def __init__(self, addr, conn=None):
        self.addr = addr
        if conn:
            self.conn = conn
        else:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(addr)
        self.buffer = b''

    def read(self):
        self.buffer += self.conn.recv(1024)
        try:
            line, self.buffer = self.buffer.split(b'\r\n', 1)     # use \r\n to split package
            line = json.loads(line.decode('utf-8'))
        except json.decoder.JSONDecodeError as e:
            self.read()
        return line[2]

    def write(self, request):
        request = json.dumps(request)
        request = request.encode('utf-8') + b'\r\n'
        self.conn.sendall(request)

    def close(self):
        self.conn.close()
