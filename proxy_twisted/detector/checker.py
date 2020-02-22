#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/21/20 11:07 PM
"""

from abc import ABCMeta, abstractmethod
import requests
from twisted.web.client import Agent, ProxyAgent
from twisted.internet.endpoints import HostnameEndpoint
from twisted.web.http_headers import Headers
import weakref
import logging

logger = logging.getLogger(__name__)


class Checker(metaclass=ABCMeta):
    @abstractmethod
    def check(self, item, asynchronous=True):
        pass
    

class BaseChecker(Checker):
    """
    check te validness of ip
    """
    @classmethod
    def produce(cls, settings):
        return cls()

    def check(self, item, asynchronous=True):
        if asynchronous:
            return self._asynchronous_check(item)
        else:
            return self._check(item)

    def _asynchronous_check(self, item):

        logger.debug('checking...')

        from twisted.internet import reactor   # must here import
        endpoint = HostnameEndpoint(reactor, item[0], int(item[1]))
        agent = ProxyAgent(endpoint)  #
        headers = {
            'User-Agent': ['Mozilla/5.0']
        }
        headers = Headers(headers)   # headers wrapper

        cd = agent.request(b'GET', b'https://www.baidu.com/', headers=headers)  # ?
        cd._connectTimeout = 3

        def check_code(response, **kwargs):
            if response.code < 300:
                logger.info('valid ip!')
                return kwargs.pop('item', None)
            else:
                raise Exception('invalid')

        def err(f):
            logger.debug(f)
            return f

        cd.addCallbacks(check_code, err, callbackKeywords={'item': item})
        # cd.addErrback(err)
        return cd

    def _check(self, item):
        try:
            resp = requests.get('https://www.baidu.com',
                                proxies={item[3]: '%s://%s:%s' % (item[3], item[0], item[1])})
            return resp.status_code
        except Exception as e:
            return 500

