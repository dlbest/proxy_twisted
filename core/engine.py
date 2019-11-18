#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""

from twisted.internet.protocol import Protocol
from twisted.internet import error
from twisted.internet.defer import Deferred, returnValue
from twisted.web.client import Agent
from twisted.python import failure
import logging
import time
from lxml import etree

connectionDone = failure.Failure(error.ConnectionDone())


class ProxyProtocol(Protocol):
    def __init__(self, deferred):
        self.result = b''
        self.d = deferred

    def dataReceived(self, data):
        self.result += data

    def connectionLost(self, reason=connectionDone):
        self.finished()

    def finished(self):
        self.d.callback(self.result)  # 引用机制的优点：可以让object传送到anywhere if u want


class Engine(object):
    pass


class Downloader(object):
    """
    把回调绑定到事件上并设置好激活条件

    """

    def __init__(self, engine, setting):
        self.engine = engine
        self.setting = setting
        self.agents = []

    @classmethod
    def produce(cls, engine, setting):
        return cls(engine, setting)

    def download(self, uri):
        return self._download(uri)

    def _download(self, uri):  # 事件可能在运行过程中已经发生，但是这个信息在reactor没有run的时候没有被捕获
        from twisted.internet import reactor
        agent = Agent(reactor)

        def get_ip(result: bytes):
            selector = etree.HTML(result, etree.HTMLParser())   # 需要修复
            return selector.xpath('//table/tbody/tr')

        def get_result(response):
            if response.code >= 300:
                returnValue('unexpected page')

            d1 = Deferred()

            response.deliverBody(ProxyProtocol(d1))
            d1.addCallback(get_ip)
            return d1

        def handle_error(fail):
            print('no')
            print(fail)

        def stop(err):
            print(err)
            from twisted.internet import reactor
            reactor.stop()

        d = agent.request(method='GET'.encode('utf-8'), uri=uri.encode('utf-8'))  #
        d.addCallbacks(get_result, handle_error)
        d.addBoth(stop)


class Checker(object):
    pass


class Pipeline(object):
    pass


if __name__ == "__main__":
    from twisted.internet import reactor

    downloader = Downloader(None, None)
    downloader.download('http://www.iphai.com/free/ng')
    reactor.run()  # 事件循环正式开始，此时信息才被处理，回调开始被激活
    # reactor.run()
