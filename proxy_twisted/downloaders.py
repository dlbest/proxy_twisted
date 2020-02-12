#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/12/20 8:48 PM
"""

from twisted.web.client import Agent, ProxyAgent      # using Agent class to realize http protocol
from twisted.internet.defer import returnValue, Deferred
from twisted.web.http_headers import Headers

from proxy_twisted.protocols import ResponseBodyProtocol
import logging
import weakref


logger = logging.getLogger(__name__)


class Downloader(object):
    """
    download the pages and scrape the item of ip
    把回调绑定到事件上并设置好激活条件

    """

    def __init__(self, engine, setting):
        logger.info('downloader is starting...')
        self.engine = weakref.ref(engine)
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
                logger.info(response.code)
                returnValue('unexpected page')   # this returnValue not likes return, it raises a exception

            def get_response(result: bytes, response):
                logger.debug('successfully downloaded '+response.request.absoluteURI.decode('utf-8'))
                logger.debug(response.code)
                response.body = result
                response.text = result.decode('utf-8')  # excellent
                return response

            d1 = Deferred()

            response.deliverBody(ResponseBodyProtocol(d1))   # need a protocol to handle response body

            d1.addCallback(get_response, response=response)   # input response there!
            return d1  # 回调链必须有返回值  d1——d

        def handle_error(fail):
            logger.warning('no')
            logger.warning(fail)

        headers = {
            'User-Agent': ['Mozilla/5.0']
        }
        headers = request.headers or headers

        headers = Headers(headers)

        d = agent.request(method=b'GET', uri=request.url.encode('utf-8'), headers=headers)
        # 当response header回传回来就会激活d，所以还需要一个处理body数据的最上层协议协议!!!

        d.addCallbacks(get_result, handle_error)
        return d
