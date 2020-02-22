#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 12/30/19 8:19 PM
"""

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from kazoo.client import KazooClient

from abc import ABCMeta, abstractmethod
import json
import weakref
import logging

from RPC_twisted.protocols import RPCFactory
from RPC_twisted.handlers import Handler
from RPC_twisted import default_settings

from RPC_twisted.utils import load_object

logger = logging.getLogger(__name__)


class Server(metaclass=ABCMeta):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class BaseServer(Server):

    """
    this class is for service
    """

    def __init__(self, host, port, interface, interface_impl, factory_cls=RPCFactory,
                 handler_cls=Handler, max_conns=-1):
        self.host = host
        self.port = port
        self.interface = interface
        if not issubclass(factory_cls, Factory):
            raise TypeError('%s is not a factory class' % str(factory_cls))
        self.factory = factory_cls(interface, interface_impl, handler_cls)
        self.factory.server = weakref.ref(self)

        from twisted.internet import reactor
        self.endpoint = TCP4ServerEndpoint(reactor, port)
        self.max_conns = max_conns

    @classmethod
    def from_settings(cls, settings: dict = None):
        if not settings:
            raise ValueError('setting cannot be None')
        else:
            host = settings.get('HOST')
            port = settings.get('PORT')
            interface = load_object(settings.get('INTERFACE'))
            interface_impl = load_object(settings.get('INTERFACE_IMPL'))
            max_counts = settings.get('MAX_COUNTS', default_settings.MAX_CONNECTIONS)

            return cls(host, port, interface, interface_impl, max_counts)

    def start(self):

        self.endpoint.listen(self.factory)
        from twisted.internet import reactor
        reactor.run()

    def stop(self):

        from twisted.internet import reactor
        if reactor.running:
            reactor.stop()

    def update_conn_counts(self, numbers, conn_name):
        if 0 < self.max_conns < numbers:
            return False
        else:
            return None


class DistributedServer(BaseServer):

    """
    this class is for distributed service
    """

    def __init__(self, host, port, interface, interface_impl, factory_cls=RPCFactory, handler_cls=Handler,
                 zk_hosts='centos01:2181,centos02:2181,centos03:2181', max_conns=-1):
        super().__init__(host, port, interface, interface_impl, factory_cls, handler_cls, max_conns)

        from twisted.internet import reactor
        self.endpoint = TCP4ServerEndpoint(reactor, port)

        self.zk = KazooClient(zk_hosts)
        self.service_path = '/DService/' + interface.__name__

    @classmethod
    def from_settings(cls, settings: dict = None):
        if not settings:
            raise ValueError('setting cannot be None')
        else:
            host = settings.get('HOST')
            port = settings.get('PORT')
            interface = load_object(settings.get('INTERFACE'))
            interface_impl = load_object(settings.get('INTERFACE_IMPL'))
            factory_cls = load_object(settings.get('RPC_PROTOCOL_FACTORY', default_settings.RPC_PROTOCOL_FACTORY))
            handler_cls = load_object(settings.get('HANDLER', default_settings.HANDLER))
            zk_hosts = settings.get('ZK_HOSTS', default_settings.ZK_HOSTS)
            max_counts = settings.get('MAX_COUNTS', default_settings.MAX_CONNECTIONS)
            return cls(host, port, interface, interface_impl, factory_cls, handler_cls, zk_hosts, max_counts)

    def start(self):
        registered = self.register_service()
        if registered:
            self.endpoint.listen(self.factory)
            from twisted.internet import reactor
            reactor.run()

    def stop(self):

        from twisted.internet import reactor
        if reactor.running:
            reactor.stop()

        self.zk.close()

    def update_conn_counts(self, numbers, conn_name):
        if 0 < self.max_conns <= numbers:
            logger.warning('connections counts reaches maximum')
            return False
        value = {'host': self.host, 'port': self.port, 'conn_counts': numbers}
        value = json.dumps(value).encode('utf-8')
        try:
            self.zk.set(self.service_path, value)
            logger.info('connections with server (%s: %s): ------%s------' % (self.host, self.port, numbers))
            return True
        except Exception as e:
            logger.error('modifying connection counts failed for %(connection)s', {'connections': conn_name},
                         exc_info=str(e))
            return False

    def register_service(self):
        try:
            self.zk.start()
        except Exception as e:
            logger.error('connecting with zk hosts failed', exc_info=str(e))
            self.stop()
        else:
            self.zk.ensure_path(self.service_path)
            value = {'host': self.host, 'port': self.port, 'conn_counts': 0}
            value = json.dumps(value).encode('utf-8')
            try:   # ephemeral node has none children nodes
                self.service_path = self.zk.create(self.service_path + '/server', value=value, ephemeral=True, sequence=True)
                logger.info('server %s:%s is registered!' % (self.host, self.port))
                return True
            except Exception as e:
                logger.error('registering failed!', exc_info=str(e))
                self.stop()



