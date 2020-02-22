#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 2/20/20 7:25 PM
"""


from RPC_twisted.dynamicProxy import ProxyFactory
from RPC_twisted.protocols import ClientTransport
from RPC_twisted.handlers import InvokeHandler
from RPC_twisted.utils import load_object
from RPC_twisted import default_settings

from kazoo.client import KazooClient

from abc import ABCMeta, abstractmethod

import json
import logging


logger = logging.getLogger(__name__)


class NoServerException(Exception):
    pass


class FactoryException(Exception):
    pass


class Client(metaclass=ABCMeta):

    @abstractmethod
    def get_proxy(self, *args, **kwargs):
        pass

    def open(self):
        pass

    def close(self):
        pass


class BaseClient(Client):
    """
    client class for one kind of service
    """

    def __init__(self, interface, proxy_factory_cls=ProxyFactory, handler_cls=InvokeHandler):
        self.interface = interface
        self.servers = {}
        self.server = None

        if not issubclass(proxy_factory_cls, ProxyFactory) or proxy_factory_cls is ProxyFactory:
            self.proxy_factory = ProxyFactory(handler_cls)
        else:
            raise FactoryException(proxy_factory_cls)

    @classmethod
    def from_settings(cls, settings: dict = None):
        if not settings:
            raise ValueError('setting cannot be None')
        else:
            interface = load_object(settings.get('INTERFACE'))
            proxy_factory_cls = load_object(settings.get('PROXY_FACTORY_CLS', default_settings.PROXY_FACTORY_CLS))
            handler_cls = load_object(settings.get('PROXY_HANDLER', default_settings.PROXY_HANDLER))
            return cls(interface, proxy_factory_cls, handler_cls)

    def get_proxy(self, host=None, port=None):

        addr = (host, port)
        _transport = ClientTransport(addr)
        logger.info('successful connect to %s:%s' % (addr[0], addr[1]))

        _proxy = self.proxy_factory(self.interface, _transport)

        return _proxy

    def open(self):
        pass

    def close(self):
        pass


class DistributedClient(BaseClient):
    """
    client class for one kind of service, equipped with zk client, realize loading balance
    """

    def __init__(self, interface, proxy_factory_cls=ProxyFactory, handler_cls=InvokeHandler,
                 zk_hosts='centos01:2181,centos02:2181,centos03:2181', service_path='/DService/'):
        super().__init__(interface, proxy_factory_cls, handler_cls)
        self.zk_hosts = zk_hosts
        self.service_path = service_path + interface.__name__
        self.zk = None

    @classmethod
    def from_settings(cls, settings: dict = None):
        if not settings:
            raise ValueError('setting cannot be None')
        else:
            interface = load_object(settings.get('INTERFACE'))
            proxy_factory_cls = load_object(settings.get('PROXY_FACTORY_CLS', default_settings.PROXY_FACTORY_CLS))
            handler_cls = load_object(settings.get('PROXY_HANDLER', default_settings.PROXY_HANDLER))
            zk_hosts = settings.get('ZK_HOSTS', default_settings.ZK_HOSTS)
            service_path = settings.get('BASE_SERVICE_PATH', default_settings.BASE_SERVICE_PATH)
            return cls(interface, proxy_factory_cls, handler_cls, zk_hosts, service_path)

    def search_service(self, zk_hosts=None, service_path=None):
        zk_hosts = zk_hosts or self.zk_hosts
        self.zk = KazooClient(zk_hosts)
        self.zk.start()
        service_path = service_path or self.service_path

        # this equals zk.ChildrenWatch(service_path)(func),func is callback, when children changes,
        # callback is activated
        @self.zk.ChildrenWatch(service_path)
        def update(children):
            if not children:
                raise NoServerException

            servers = dict(zip(children, [None] * len(children)))
            for x in servers:
                if x in self.servers:
                    servers[x] = self.servers[x]
                else:
                    node_path = service_path + '/' + x

                    @self.zk.DataWatch(node_path)
                    def update_data(data, stat, *args):
                        data = json.loads(data.decode('utf-8'))
                        servers[x] = self.servers[x] = data
                        self.server = min(self.servers, key=lambda i: self.servers[i]['conn_counts'])
            self.servers = servers
            logger.debug(self.servers)

    def get_proxy(self, host=None, port=None):

        node = self.servers[self.server]
        addr = (node['host'], node['port'])
        _transport = ClientTransport(addr)
        logger.info('successful connect to %s:%s' % (addr[0], addr[1]))

        _proxy = self.proxy_factory(self.interface, _transport)

        return _proxy

    def open(self, *args, **kwargs):
        self.search_service(*args, **kwargs)

    def close(self):
        self.zk.close()
