#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""

from proxy_twisted.engine import Engine
from proxy_twisted import settings
import logging
from twisted.internet import reactor

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    eng = Engine(settings)
    d = eng.start([r'https://www.xicidaili.com/nn/%d' % i for i in range(1, 11)])


    def pp(result):
        logger.debug(result)
        reactor.stop()


    d.addBoth(pp)
    reactor.run()  # 事件循环正式开始，此时信息才被处理，回调开始被激活

    # downloader = Downloader(None, None)
    # downloader.download(r'https://www.xicidaili.com/nn')
    # reactor.run()

