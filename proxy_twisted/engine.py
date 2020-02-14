#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""


from twisted.internet.defer import Deferred, returnValue, succeed, DeferredList, inlineCallbacks

from twisted.internet import reactor

import sys
from queue import Queue
from proxy_twisted.utils import load_object   # low coupling

import logging


# 解决ssl验证失败问题
from twisted.internet import _sslverify

_sslverify.platformTrust = lambda: None

logger = logging.getLogger(__name__)


class Item(dict):
    pass


class Scheduler(object):
    def __init__(self, engine, settings):
        self.queue = Queue()

    @classmethod
    def produce(cls, engine, settings):
        return cls(engine, settings)

    def dequeue_request(self, block=False, timeout=0):
        return self.queue.get(block=block, timeout=timeout)

    def enqueue_request(self, request, block=False, timeout=0):
        return self.queue.put(request, block=block, timeout=timeout)


class Engine(object):

    def __init__(self, settings):
        self.alive_requests = []
        self.setting = settings
        component = getattr(settings, 'COMPONENT', None)
        self.component = {}
        if component:
            for i in component:
                self.component[i] = load_object(component[i]).produce(self, setting)
                # self.component[i] = getattr(sys.modules[__name__], i, None).produce(self, setting)
                # using produce class method like using factory

    @classmethod
    def produce(cls, settings):
        return cls(settings)

    def start(self, urls, concurrent=1, delay=30):
        deferred_list1 = []
        requests = self.component['Spider'].get_request(urls)
        self.enqueue_request(requests)
        alive_requests = self.fire_request(concurrent)
        for request in alive_requests:
            d = self.download(request, delay)
            deferred_list1.append(d)
        return DeferredList(deferred_list1)  # 待所有的deferred元素都激活返回后，才会激活deferred list

    @inlineCallbacks
    def download(self, request, delay=0):
        """
        download the page and scrape the item
        """

        def get_item(items):
            logger.info(items)
            deferred_list = []
            for item in items:
                check_d = self.component['Checker'].check(item)
                check_d.addCallback(self.component['Pipeline'].process_item)
                check_d.addErrback(lambda x: print(x, '----------------------------------------------'))
                deferred_list.append(check_d)
            dl = DeferredList(deferred_list)
            return dl

        dd = self.component['Downloader'].download(request)
        dd.addCallback(self.component['Spider'].parse)
        dd.addCallback(lambda x: list(x))
        dd.addCallback(get_item)
        dd.addBoth(self.update_alive_request, request, delay)
        dd.addBoth(lambda x: logger.debug(x))
        yield dd

    def enqueue_request(self, requests):
        scheduler = self.component['Scheduler']
        for request in list(requests):
            scheduler.enqueue_request(request, block=True, timeout=3)

    def fire_request(self, count=1):
        for i in range(count):
            request = self.component['Scheduler'].dequeue_request(block=False)
            self.alive_requests.append(request)
            yield request

    def update_alive_request(self, _, request, delay=0):
        logger.info('downloading' + request.url + 'is finished!')
        self.alive_requests.remove(request)
        request = next(self.fire_request(1))
        logger.debug('fire new requests')
        ddd = Deferred()
        ddd.addCallback(self.download, delay)
        reactor.callLater(delay, ddd.callback, request)  # 注册一个事件而已
        return ddd


