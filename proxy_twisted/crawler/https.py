#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/12/20 8:07 PM
"""


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
