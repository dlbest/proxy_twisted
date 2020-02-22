#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/21/20 7:49 PM
"""

import pymysql
import logging

from abc import ABCMeta, abstractmethod
from twisted.internet import defer
from twisted.enterprise import adbapi

from proxy_twisted.detector.checker import BaseChecker
from proxy_twisted.utils import load_object

logger = logging.getLogger(__name__)


class Detector(metaclass=ABCMeta):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def detect(self):
        pass

    @abstractmethod
    def get_result(self):
        pass


class BaseDetector(Detector):
    def __init__(self, c, settings):
        self.checker = load_object(c).produce(settings)
        self.invalid_ips = []
        self.pool = None
        self.params = {
            'host': '192.168.1.55',
            'port': 3306,
            'user': 'root',
            'password': '931121',
            'database': 'ipools',
            'charset': 'utf8',
            'use_unicode': True,
            'cursorclass': pymysql.cursors.Cursor
        }
        self.pool = None
        self.pool_capacity = settings.CAPACITY
        self.current_counts = 0

    @classmethod
    def produce(cls, settings):
        return cls(**settings.DETECTOR_CONFIG, settings=settings)

    def start(self):
        pass

    def close(self, result):
        if self.current_counts < self.pool_capacity:
            return self.invalid_ips + self.pool_capacity - self.current_counts

    def detect(self, sql='select ip, port, id from xici'):
        self.invalid_ips = 0
        self.pool = adbapi.ConnectionPool('pymysql', **self.params)
        d = self.pool.runInteraction(self.execute, sql)
        d.addCallback(self.check_all)
        return d

    def get_result(self):
        pass

    def execute(self, cursor, *args):
        cursor.execute(*args)
        res = cursor.fetchall()
        self.current_counts = len(res)
        return res

    def check_all(self, items):
        deferred_list = []
        if not items:
            self.invalid_ips = self.pool_capacity
            d = defer.succeed(None)
            d.addCallback(self.close)
            return d
        for item in items:
            res = self.check(item)
            res.addErrback(self.update_db, item=item)
            deferred_list.append(res)
        d = defer.DeferredList(deferred_list)
        d.addBoth(self.close)
        return d

    def check(self, item):
        return self.checker.check(item)

    def update_db(self, _, item):

        self.invalid_ips += 1
        sql = 'delete from ipool1 where id=%s'
        res = self.pool.runInteraction(self.execute, sql, item[2])
        res.addCallbacks(callback=lambda _: logger.info('delete ip: %(item)s successfully', {'item': item}),
                         errback=lambda _: logger.info('failed to delete ip: %(item)s', {'item': item},
                                                       exc_info=str(_)))


