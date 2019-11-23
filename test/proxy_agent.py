"""
@project:proxy_twisted
@author: momentum
@time:20191120
"""


from twisted.web.client import ProxyAgent
from twisted.internet import reactor
from twisted.internet.endpoints import HostnameEndpoint


endpoint = HostnameEndpoint(reactor, '27.43.191.21', '9999')
agent = ProxyAgent(endpoint)
d = agent.request(b'GET', b'https://www.baidu.com/')
d._connectTimeout = 10
d.addBoth(print)
reactor.run()