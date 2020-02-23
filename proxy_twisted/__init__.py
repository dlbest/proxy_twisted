#!usr/bin/env python

"""
@PROJECT = "proxy_twisted"
@AUTHOR = "momentum"
@DATETIME = "11/12/19 10:11 PM"
"""


import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s %(lineno)s]: %(levelname)s: %(message)s')

from RPC_twisted import ServerBuilder   # u need a rpc framework!
from proxy_twisted.crawler.engine import Engine
from proxy_twisted import settings
from proxy_twisted.server.server import Server
from proxy_twisted.server.interface import IPInterface, IPInterfaceImpl


logger = logging.getLogger(__name__)


def start_poll_pool_service():
    crawler_cls = settings.CRAWLER_CLS
    detector_cls = settings.DETECTOR_CLS
    s = Server(crawler_cls, detector_cls, settings)
    s.start()


def start_ip_service():

    obj = IPInterfaceImpl.produce(settings)
    obj.start()
    builder = ServerBuilder(IPInterface, obj)
    s = builder.build('0.0.0.0', 22222)
    s.start()


if __name__ == '__main__':
    import multiprocessing
    p1 = multiprocessing.Process(target=start_poll_pool_service)
    p1.start()

    p2 = multiprocessing.Process(target=start_ip_service)
    p2.start()

    p1.join()
    p2.join()




































# if __name__ == "__main__":
#     eng = Engine(settings)
#     d = eng.start([r'https://www.xicidaili.com/nn/%d' % i for i in range(1, 11)])
#
#
#     def pp(result):
#         logger.debug(result)
#         reactor.stop()
#
#
#     d.addBoth(pp)
#     reactor.run()  # 事件循环正式开始，此时信息才被处理，回调开始被激活
#
#     # downloader = Downloader(None, None)
#     # downloader.download(r'https://www.xicidaili.com/nn')
#     # reactor.run()
#
