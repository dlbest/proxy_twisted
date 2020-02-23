"""
@project:proxy_twisted
@author: momentum
@time:20191120
"""


from twisted.web.client import ProxyAgent
from twisted.internet import reactor, defer, task
from twisted.internet.endpoints import HostnameEndpoint
from multiprocessing import Process
import os


from RPC_twisted import DistributedClient
from proxy_twisted.server.interface import IPInterface


c = DistributedClient(IPInterface)
c.open()
p = c.get_proxy()
for i in range(10):
    print(p.get_ip(num=1))
p.close()

# def kk(t):
#     print(t)
#     from twisted.internet import reactor
#     q = id(reactor)
#     print('ci-kk:', q)
#     reactor.stop()
# #
# #
# def printf(x):
#     print('b', x, os.getpid())
#     # from twisted.internet.main import installReactor
#     # from twisted.internet.epollreactor import EPollReactor
#     # p = EPollReactor()
#     # import sys
#     # sys.modules.pop('twisted.internet.reactor')
#     # installReactor(p)
#     from twisted.internet import reactor
#     q = id(reactor)
#     print('ci--p:', q)
#     reactor.callLater(3, kk, 'hahaa')
#
#     reactor.run()
# #
# #
# def a(r):
#     print('a', r)
#     p = Process(target=printf, args=(2,))
#     p.start()
#     from twisted.internet import reactor
#     q = id(reactor)
#     print('zhu:--a', q)
#     # return None
#
#
#
# while True:
#     a(1)
#     import time
#     time.sleep(1)

# d = defer.Deferred()
# d.addCallback(a)
# d.addCallback(print, 'dasd')
#


# task = task.LoopingCall(a, '1')
#
# task.start(50)
#
# from twisted.internet import reactor
# w = id(reactor)
# print('zhu--m:', w)
# reactor.run()   # just a block, loop
# print('yes')

# from multiprocessing import Process
#
#
# class A:
#     def __init__(self, k):
#         self.counts = k
#
#     def add(self, i):
#         print(id(self))
#         self.counts += i
#         self.r = 2
#         print(self.counts)
#         print(id(self))
#
#
# a = A(1)
# print(id(a))
# print(a.counts)
# p = Process(target=a.add, args=(1,))
# p.start()
# p.join()
#
#
# print(a.r)

#
# import sys, multiprocessing
# print('zhu:', sys.modules)
#
#
# def printf():
#     import sys
#
#     sys.modules['dasd']='hahahah_______________________'
#     print('ci', sys.modules)
#
# p = multiprocessing.Process(target=printf)
# p.start()
# p.join()
#
# import sys
# print('zhu:', sys.modules)

