#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/22/20 12:43 AM
"""

import multiprocessing
import pymysql
from twisted.internet import defer, task
from proxy_twisted.utils import load_object
import logging

logger = logging.getLogger(__name__)


class Server(object):
    """
    1. poll the ip pool and start a crawling task
    2. ip service
    """

    def __init__(self, crawler_cls, detector_cls, settings):
        self.ips = []
        self.crawler_cls = crawler_cls
        self.detector_cls = detector_cls
        self.crawler = None
        self.detector = None
        self.checker = None
        self.mysql_cli = None
        self.settings = settings

    @classmethod
    def produce(cls, settings):
        crawler_cls = settings.CRAWLER_CLS
        detector_cls = settings.DETECTOR_CLS
        return cls(crawler_cls, detector_cls, settings)

    def start(self, poll=True, interval=7200, ip_cache=3):
        self.crawler = load_object(self.crawler_cls).produce(self.settings)

        if poll:
            self.detector = load_object(self.detector_cls).produce(self.settings)
            call = task.LoopingCall(self.update_ip_pool)
            call.start(interval)
            from twisted.internet import reactor
            logger.debug('server' + str(id(reactor)))
            reactor.run()
        else:
            self.checker = load_object(self.settings.CHECKER_CLS).produce(self.settings)
            self.ips = self.get_ips(ip_cache)

    def close(self, result):
        pass

    def update_ip_pool(self):
        d = self.start_detect_task()
        d.addCallback(self.start_crawl_task)
        d.addCallback(lambda _: 'update task finished')

    def start_detect_task(self):

        return self.detector.detect()

    def start_crawl_task(self, num):
        # how to generate a new process with async thread from a process with async thread,
        # have multi reactors instance in multi process
        # in subprocess, which will copy all object data from process?? we need to instantiate a new reactor

        def _task(n):
            # how to realize a new reactor
            from twisted.internet.main import installReactor
            from twisted.internet.epollreactor import EPollReactor
            reactor = EPollReactor()
            import sys
            del sys.modules['twisted.internet.reactor']
            installReactor(reactor)
            from twisted.internet import reactor
            ######################################################
            logger.debug('task' + str(id(reactor)))

            self.crawler.crawl(n)
            self.crawler.start()

        if num:
            p = multiprocessing.Process(target=_task, args=(num,))  # use a new process to execute crawl task
            p.start()
            # p.join()   # join will block, waiting for p finished

    def get_ips(self, num):
        mysql_cli = pymysql.connect(host='192.168.1.55', user='root', passwd='931121', db='ipools', charset='utf8')
        cursor = mysql_cli.cursor()
        cursor.execute('select ip, port, id, protocol from xici order by rand() limit %s', num)
        ips = cursor.fetchall()
        result = []
        for ip in ips:
            if self.checker.check(ip, False) > 300:
                cursor.execute('delete from ipool1 where id=%s', ip[2])
                self.get_ip(1)
            else:
                result.append((ip[0], ip[1]))
        mysql_cli.close()
        return result

    def update_ip_cache(self):
        self.ips = self.get_ips(50)
