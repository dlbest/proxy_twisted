#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/21/20 7:49 PM
"""


from abc import ABCMeta, abstractmethod

from twisted.internet.defer import inlineCallbacks
import logging

from proxy_twisted.utils import load_object

logger = logging.getLogger(__name__)


class Crawler(metaclass=ABCMeta):

    @abstractmethod
    def crawl(self, url, requirement=0):
        pass

    @abstractmethod
    def start(self):
        pass


class BaseCrawler(Crawler):
    def __init__(self, engine_cls, spider_cls, settings):
        self.engine_cls = engine_cls
        self.settings = settings
        self.spider_cls = spider_cls

    @classmethod
    def produce(cls, settings):
        return cls(settings.ENGINE_CLS, settings.SPIDER_CLS, settings)

    @inlineCallbacks
    def crawl(self, requirement=0):
        logger.info('start a crawling task!, required: %(num)s', {'num': requirement})
        engine = load_object(self.engine_cls).produce(self.settings)   # local variable gc?
        spider = load_object(self.spider_cls).produce(self.settings)
        requests = spider.start_requests()
        yield engine.start(requests, spider, requirement, )

    def start(self):
        from twisted.internet import reactor
        logger.debug('task' + str(id(reactor)))
        reactor.run()


if __name__ == '__main__':
    from proxy_twisted import settings as s
    c = BaseCrawler.produce(s)
    c.crawl(3)
    c.start()
