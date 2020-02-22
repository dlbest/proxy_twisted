#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 2/12/20 11:59 PM
"""


# zk information
ZK_HOSTS = 'centos01:2181,centos02:2181,centos03:2181'

# service_path
BASE_SERVICE_PATH = '/DService/'


# server endpoint protocol factory class
RPC_PROTOCOL_FACTORY = 'RPC_twisted.protocols.RPCProtocol'

# server endpoint handler
HANDLER = 'rpc_twisted.handlers.HANDLER'

# server endpoint max connections
MAX_CONNECTIONS = -1


# client endpoint proxy factory
PROXY_FACTORY_CLS = 'RPC_twisted.dynamicProxy.ProxyFactory'

# client endpoint handler
PROXY_HANDLER = 'RPC_twisted.handlers.InvokeHandler'











