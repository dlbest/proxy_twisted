#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/12/20 8:28 PM
"""


from twisted.web.client import Agent, ProxyAgent
from twisted.internet.endpoints import HostnameEndpoint
from twisted.web.http_headers import Headers
from twisted.internet import reactor

from twisted.enterprise import adbapi
import pymysql
import logging
import weakref

logger = logging.getLogger(__name__)


class Pipeline(object):
    """
    process the scraped item
    """

    def __init__(self, pool: adbapi.ConnectionPool, engine, settings):
        logger.info('pipeline is starting')
        self.pool = pool
        self.engine = weakref.ref(engine)
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

    def process_item(self, item):
        if item:
            d = self.pool.runInteraction(self.insert_item, item)
            d.addErrback(self.handle_err)
            return item
        else:
            raise ValueError('item is None!')

    @staticmethod
    def insert_item(self, cursor, item):
        item = (item[0], item[1], item[3], item[5], item[6], item[11], item[12])
        sql = """insert into xici(ip, port, location, security, protocol, life, valid_date) 
        values(%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, item)

    @staticmethod
    def handle_err(self, err):
        logger.error('error:', exc_info=err)


class Checker(object):
    """
    check te validness of ip
    """

    def __init__(self, engine, settings):
        logger.info('checker is starting')
        self.engine = weakref.ref(engine)
        self.setting = settings

    @classmethod
    def produce(cls, engine, settings):
        return cls(engine, settings)

    def check(self, item):
        return self._check(item)

    def _check(self, item):
        logger.debug('checking...')
        item[1] = int(item[1])
        endpoint = HostnameEndpoint(reactor, item[0], item[1])
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

        cd.addCallbacks(check_code, errback=err, callbackKeywords={'item': item})
        return cd
