"""
@project:proxy_twisted
@author: momentum
@time:20191120
"""


from twisted.web.client import ProxyAgent
from twisted.internet import reactor, defer
from twisted.internet.endpoints import HostnameEndpoint


d = defer.Deferred()
d.addCallback()
