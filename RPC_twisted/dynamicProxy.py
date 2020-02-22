#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 1/1/20 4:10 PM


"""

from types import FunctionType
import weakref

from RPC_twisted.handlers import HandlerException, InvokeHandler

import logging

logger = logging.getLogger(__name__)


class Proxy(object):

    """
    this class is proxy which process data and transfer attribute calling, for a interface class
    a special protocol class
    """

    def __init__(self, cls, hcls, transport):
        self.cls = cls
        self.hcls = hcls
        self.transport = transport
        self.handlers = dict()

    def __getattr__(self, item):
        """

        :param item: item should be a method of cls
        :return: res is a callable object which replacing item
        """
        is_exist = hasattr(self.cls, item)
        res = None
        if is_exist:
            res = getattr(self.cls, item)
            if isinstance(res, FunctionType):
                if self.handlers.get(res) is None:
                    self.handlers[res] = self.hcls(self, self.cls, res)
                    return self.handlers[res]
                else:
                    return self.handlers[res]
            else:
                return res
        return res

    def close(self):
        self.transport.close()
        del self


class ProxyFactory(object):
    proxy = Proxy

    def __init__(self, hcls):
        if issubclass(InvokeHandler, hcls) or hcls is InvokeHandler:
            self.hcls = hcls
        else:
            raise HandlerException(hcls)

    def __call__(self, interface, transport, *args, **kwargs):
        """
        call it, return a proxy for a transport
        :param cls: interface class
        :param transport: a connection
        :param args:
        :param kwargs:
        :return: a Proxy instance
        """

        _proxy = self.proxy(interface, self.hcls, transport)
        _proxy.factory = weakref.ref(self)
        return _proxy








