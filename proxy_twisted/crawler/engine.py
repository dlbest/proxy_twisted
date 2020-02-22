#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""


from twisted.internet import task, defer
from twisted.internet.defer import DeferredList, inlineCallbacks
from twisted.internet import _sslverify  # 解决ssl验证失败问题

from proxy_twisted.utils import load_object   # low coupling
from proxy_twisted.crawler.https import Request
from proxy_twisted import signals

import time
import logging

_sslverify.platformTrust = lambda: None

logger = logging.getLogger(__name__)


class Engine(object):

    def __init__(self, scheduler, downloader, checker, pipeline, signal, concurrent=1, settings=None):
        self.signal = load_object(signal)
        self.alive_requests = []
        self.scheduler = load_object(scheduler).produce(self, settings)
        self.downloader = load_object(downloader).produce(self, settings)
        self.checker = load_object(checker).produce(self, settings)
        self.pipeline = load_object(pipeline).produce(self, settings)
        self.concurrent = concurrent
        self.alive_requests = 0
        self.settings = settings
        self.item_counts = 0
        self.required = 0
        self.idle = 0
        self.idle_before_close = 0
        self.spider = None
        self.closed = True

    @classmethod
    def produce(cls, settings):
        engine_config = settings.ENGINE_CONFIG
        engine = cls(**engine_config, settings=settings)

        engine.signal.connect(engine.update_requests_counts, signals.REQUEST_CRAWLED)
        engine.signal.connect(engine.update_item_counts, signals.ITEM_PROCESSED)
        return engine

    def start(self, requests, spider, item_counts=10, delay=3, idle_before_close=240):
        self.closed = False
        self.required = item_counts
        self.idle_before_close = idle_before_close
        self.enqueue_request(requests)
        self.next_request(spider)
        next_call = task.LoopingCall(self.next_request, spider=spider)
        next_call.start(delay)

    def stop(self, spider):
        logger.info('finally cralwer item: %(counts)s', {'counts': self.item_counts})

        from twisted.internet import reactor
        logger.debug('task' + str(id(reactor)))
        reactor.stop()   # all coroutine are interrupted

    def next_request(self, spider):

        self.spider = spider
        while self.alive_requests < self.concurrent:
            try:
                request = self.scheduler.dequeue_request(block=True, timeout=1)
            except Exception as e:

                if not self.idle:
                    self.idle = time.time()
                    return None
                elif (time.time() - self.idle >= self.idle_before_close) or (self.item_counts > self.required):
                    if not self.closed:
                        logger.error('can not get requests during valid times', exc_info=str(e))
                        self.closed = True
                        self.stop(spider)
                else:
                    return None
            else:
                self.idle = 0
                self.alive_requests += 1
                self.download(request, spider)

    # return a fired deferred
    @inlineCallbacks
    def download(self, request, spider=None):
        """
        download the page and scrape the item
        """

        def get_item(items):
            logger.info(items)
            self.signal.send(signals.REQUEST_CRAWLED, num=1)

            deferred_list = []
            for item in items:
                if isinstance(item, Request):
                    self.enqueue_request((item, ))
                else:
                    d = defer.succeed(item)
                    d.addCallback(self.checker.process_item, spider=spider)
                    d.addCallback(self.pipeline.process_item, spider=spider)
                    d.addErrback(lambda x: print(x, '----------------------------------------------'))
                    deferred_list.append(d)
            dl = DeferredList(deferred_list)   # 待所有的deferred元素都激活返回后，才会激活deferred list
            return dl

        dd = self.downloader.download(request, spider)
        # dd.addCallback(lambda x: list(x))
        dd.addCallback(get_item)
        dd.addCallback(lambda x: logger.debug('crawling request: %(request)s is finished!', {'request': request}))
        dd.addErrback(lambda x: logger.error('crawling request: %(request)s has error!',
                                             {'request': request}, exc_info=x))
        yield dd

    def enqueue_request(self, requests):
        scheduler = self.scheduler
        for request in list(requests):
            scheduler.enqueue_request(request, block=False)

    def update_requests_counts(self, num):
        self.alive_requests -= num

    def update_item_counts(self):
        self.item_counts += 1

