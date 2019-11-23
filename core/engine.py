#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""

from twisted.internet.protocol import Protocol
from twisted.internet import error
from twisted.internet.defer import Deferred, returnValue, succeed, DeferredList, inlineCallbacks
from twisted.web.client import Agent, ProxyAgent
from twisted.web.http_headers import Headers
from twisted.internet.endpoints import HostnameEndpoint
from twisted.python import failure
from twisted.internet import reactor
import logging
from lxml import etree
from twisted.enterprise import adbapi
import pymysql
import sys
from queue import Queue
import settings

# 解决ssl验证失败问题
from twisted.internet import _sslverify

_sslverify.platformTrust = lambda: None

logging.basicConfig(**{'level': 0})
connectionDone = failure.Failure(error.ConnectionDone())


class Item(dict):
    pass


class Request(object):
    """
    wrapper of a request
    dict-like：__getitem__, __setitem__, __delitem__
    """

    def __init__(self, url, method='GET', protocol='HTTP/1.1', headers=None, body=None, callback=None, errback=None):
        self.url = url
        self.method = method
        self.protocol = protocol
        self.headers = headers
        self.body = body
        self.callback = callback
        self.errback = errback

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        self.__delattr__(key)

    def get(self, item, default=None):
        try:
            return self.__getitem__(item)
        except KeyError:
            return default


class Response(Request):
    """
    wrapper of a response
    """

    def __init__(self, url, request, status_code, headers, body):
        self.url = url
        self.request = request
        self.status_code = status_code
        self.headers = headers
        self.body = body


class ProxyProtocol(Protocol):
    """
    a protocol for response body data
    """

    def __init__(self, deferred):
        self.result = b''
        self.d = deferred

    def dataReceived(self, data):
        self.result += data

    def connectionLost(self, reason=connectionDone):
        self.finished()

    def finished(self):
        self.d.callback(self.result)  # 引用机制的优点：可以让object传送到anywhere if u want


class Scheduler(object):
    def __init__(self, engine, setting):
        self.queue = Queue()

    @classmethod
    def produce(cls, engine, setting):
        return cls(engine, setting)

    def get(self):
        return self.queue.get(block=False)

    def put(self, request):
        return self.queue.put(request, block=False)


class Engine(object):

    def __init__(self, setting):
        self.alive_requests = []
        self.setting = setting
        component = getattr(setting, 'COMPONENT', None)
        self.component = {}
        if component:
            for i in component:
                self.component[i] = getattr(sys.modules[__name__], i, None).produce(self, setting)

    def start(self, urls, concurrent=5, delay=30):
        deferred_list1 = []
        requests = self.component['Spider'].get_request(urls)
        self.enqueue_request(requests)
        alive_requests = self.fire_request(concurrent)
        for request in alive_requests:
            d = self.download(request, delay)
            deferred_list1.append(d)
        return DeferredList(deferred_list1)  # 待所有的deferred元素都激活返回后，才会激活deferred list

    @inlineCallbacks
    def download(self, request, delay):
        """
        download the page and scrape the item
        """

        def get_item(items):
            logging.info(items)
            deferred_list = []
            for item in items:
                check_d = self.component['Checker'].check(item)
                check_d.addCallback(self.component['Pipeline'].process_item)
                deferred_list.append(check_d)
                return DeferredList(deferred_list)

        dd = self.component['Downloader'].download(request)
        dd.addCallback(self.component['Spider'].parse)
        dd.addCallback(lambda x: list(x))
        dd.addCallback(get_item)
        dd.addBoth(self.update_alive_request, request, delay)
        dd.addBoth(lambda x: print('+++++++++++++++', x))
        yield dd

    def enqueue_request(self, requests):
        scheduler = self.component['Scheduler']
        for request in list(requests):
            scheduler.queue.put(request, block=True)

    def fire_request(self, count=5):
        for i in range(count):
            request = self.component['Scheduler'].queue.get(block=False)
            self.alive_requests.append(request)
            yield request

    def update_alive_request(self, _, request, delay=0):
        self.alive_requests.remove(request)
        request = next(self.fire_request(1))
        logging.debug('fire new requests')
        ddd = Deferred()
        ddd.addCallback(self.download)
        reactor.callLater(delay, ddd.callback, request, delay)  # 注册一个事件而已
        return ddd


class Downloader(object):
    """
    download the pages and scrape the item of ip
    把回调绑定到事件上并设置好激活条件

    """

    def __init__(self, engine, setting):
        logging.info('downloader is starting...')
        self.engine = engine
        self.setting = setting

    @classmethod
    def produce(cls, engine, setting):
        return cls(engine, setting)

    def download(self, request):
        return self._download(request)

    def _download(self, request):  # 事件可能在运行过程中已经发生，但是这个信息在reactor没有run的时候没有被捕获
        from twisted.internet import reactor
        agent = Agent(reactor)

        def get_result(response):
            if response.code >= 300:
                logging.info(response.code)
                returnValue('unexpected page')

            def get_response(result: bytes):
                logging.debug('successfully downloaded '+response.request.url)
                logging.info(response.code)
                response.body = result
                response.text = result.decode('utf-8')  # excellent
                return response

            d1 = Deferred()

            response.deliverBody(ProxyProtocol(d1))
            d1.addCallback(get_response)
            return d1  # 回调链必须有返回值  d1——d

        def handle_error(fail):
            logging.warning('no')
            logging.warning(fail)

        headers = {
            'User-Agent': ['Mozilla/5.0']
        }
        headers = Headers(request.headers)

        d = agent.request(method=b'GET', uri=request.url.encode('utf-8'), headers=headers)
        # 当header回传回来就会激活d，所以还需要一个处理body数据的最上层协议协议
        d.addCallbacks(get_result, handle_error)
        return d


class Checker(object):
    """
    check te validness of ip
    """

    def __init__(self, engine, setting):
        logging.info('checker is starting')
        self.engine = engine
        self.setting = setting

    @classmethod
    def produce(cls, engine, setting):
        return cls(engine, setting)

    def check(self, item):
        return self._check(item)

    def _check(self, item):
        logging.debug('check+++' + item)
        item[1] = int(item[1])
        endpoint = HostnameEndpoint(reactor, item[0], item[1])
        agent = ProxyAgent(endpoint)  #
        headers = {
            'User-Agent': ['Mozilla/5.0']
        }
        headers = Headers(headers)
        d = agent.request(b'GET', b'https://www.baidu.com/', headers=headers)  # ?
        d._connectTimeout = 10

        def check_code(response):
            if response.code < 300:
                return item
            else:
                raise Exception('invalid')

        d.addCallback(check_code)
        return d


class Pipeline(object):
    """
    process the scraped item
    """

    def __init__(self, pool: adbapi.ConnectionPool, engine, setting):
        logging.info('pipeline is starting')
        self.pool = pool
        self.engine = engine
        self.setting = setting

    @classmethod
    def produce(cls, engine, setting):
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
        return cls(pool, engine, setting)

    def process_item(self, item):
        d = self.pool.runInteraction(self.insert_item, item)
        d.addErrback(self.handle_err)
        return item

    def insert_item(self, cursor, item):
        sql = """insert into ipool1(ip, port, location, security, protocol, reaction, valid_date) 
        values(%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, item)

    def handle_err(self, err):
        logging.error('error:', exc_info=err)


class Spider(object):
    def __init__(self, engine, setting):
        logging.info('parser is starting...')
        self.setting = setting

    @classmethod
    def produce(cls, engine, setting):
        return cls(engine, setting)

    def get_request(self, urls):
        for url in urls:
            yield Request(url, headers={'user-agent': ['Mozilla/5.0']}, callback=self.parse)

    def parse(self, response):
        logging.info('parsing...')
        return self._parse(response)

    def _parse(self, response):
        logging.debug(response)
        selector = etree.HTML(response.text, etree.HTMLParser())  # 需要修复
        logging.debug(selector)
        nodes = selector.xpath(r'//table/tr')
        for node in nodes:
            result = node.xpath(r'td/text()')
            logging.debug(result)
            if result:
                logging.debug('successfully get an item')
                yield result


if __name__ == "__main__":
    eng = Engine(settings)
    d = eng.start([r'https://www.xicidaili.com/nn/%d' % i for i in range(10)])


    def pp(result):
        logging.debug(result)
        reactor.stop()


    d.addBoth(pp)
    reactor.run()  # 事件循环正式开始，此时信息才被处理，回调开始被激活

    # downloader = Downloader(None, None)
    # downloader.download(r'https://www.xicidaili.com/nn')
    # reactor.run()
