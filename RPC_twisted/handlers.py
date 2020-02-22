#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 2/13/20 7:53 PM
"""

from abc import ABCMeta, abstractmethod

import weakref
import logging

logger = logging.getLogger(__name__)


class HandlerException(Exception):
    def __init__(self, cls):
        super().__init__(cls, "is not a handler class")


class BaseHandler(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class Handler(BaseHandler):
    """
    server endpoint
    ====================
    handler class, for data response
    """

    def __init__(self, protocol, interface, interface_impl):
        self.protocol = weakref.ref(protocol)          # weak reference
        setattr(self, interface.__name__, interface)
        if type(interface_impl) == type:
            self.interface_impl_obj = interface_impl()
        else:
            self.interface_impl_obj = interface_impl

    def __call__(self, line):
        result = ''
        if hasattr(self, line[0]):
            try:
                result = getattr(self.interface_impl_obj, line[1])(**line[3])   # reflection
            except Exception as e:
                logger.error('call failed', exc_info=str(e))
                result = 'error: %s' % e
            finally:
                return line[0], line[1], result
        else:
            return line[0], line[1], 'no such service'


class InvokeHandler(BaseHandler):
    """
    client endpoint
    ==========================
    this class is for wrapping the func called once
    """

    def __init__(self, proxy, obj, func):
        self.proxy = weakref.ref(proxy)
        self.obj = obj
        self.func = func

    def __call__(self, *args, **kwargs):
        """
        this magic method is key, proxy the method called
        :param args:
        :param kwargs:
        :return:
        """
        request = (self.obj.__name__, self.func.__name__, args, kwargs)  # get name to reflect
        proxy = self.proxy()
        proxy.transport.write(request)
        response = proxy.transport.read()
        del proxy
        return response
