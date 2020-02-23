#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/12/20 8:28 PM
"""


import pymysql
import logging
import weakref
from abc import ABCMeta, abstractmethod, ABC

from twisted.enterprise import adbapi

from proxy_twisted import signals
from proxy_twisted.detector.checker import BaseChecker


logger = logging.getLogger(__name__)


class Pipeline(metaclass=ABCMeta):
    @abstractmethod
    def produce(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def process_item(self, item, spider):
        pass
    
    
class MysqlPipeline(Pipeline):
    """
    process the scraped item
    """

    def __init__(self, pool: adbapi.ConnectionPool, engine, settings):
        logger.info('pipeline is starting')
        self.pool = pool
        self.engine = weakref.ref(engine)
        self.signal = engine.signal
        self.settings = settings

    @classmethod
    def produce(cls, engine, settings):
        params = {
            'host': '192.168.1.55',
            'port': 3306,
            'user': 'root',
            'password': '931121',
            'database': 'ipools',
            'charset': 'utf8',
            'use_unicode': True,
            'cursorclass': pymysql.cursors.DictCursor
        }
        pool = adbapi.ConnectionPool('pymysql', **params)
        return cls(pool, engine, settings)

    def process_item(self, item, spider):
        if item:
            d = self.pool.runInteraction(self.insert_item, item)
            d.addCallbacks(self.succeed, self.handle_err)
            # send signals
            self.signal.send(signals.ITEM_PROCESSED)
            return item
        else:
            raise ValueError('item is None!')

    def insert_item(self, cursor, item):
        item = (item[0], item[1], item[3], item[5], item[6], item[11], item[12])
        sql = """insert into xici(ip, port, location, security, protocol, life, valid_date) 
        values(%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, item)

    def succeed(self, res):
        logger.info('successfully push item into mysql!')

    def handle_err(self, err):
        logger.error('error:', exc_info=err)


class CPipeline(Pipeline, BaseChecker):
    
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def produce(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def process_item(self, item, spider):
        res = self.check(item)
        return res
        # logger.debug('item....')
        # return item
