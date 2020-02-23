#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/22/20 12:43 AM
"""

import logging
import random
from abc import ABCMeta, abstractmethod
from twisted.internet import task

from proxy_twisted.utils import load_object

logger = logging.getLogger(__name__)


class IPInterface(metaclass=ABCMeta):
    @abstractmethod
    def get_ip(self, num):
        pass


class IPInterfaceImpl(IPInterface):
    def __init__(self, provider):
        self.provider = provider

    @classmethod
    def produce(cls, settings):
        provider = load_object(settings.SERVER_CLS).produce(settings)
        return cls(provider)

    def start(self, interval=1800):
        """

        :param interval: how long update the ip cache
        :return:
        """
        self.provider.start(False)
        t = task.LoopingCall(self.provider.update_ip_cache)
        t.start(interval)

    def get_ip(self, num):
        if num <= len(self.provider.ips):
            random.shuffle(self.provider.ips)
            return self.provider.ips[:num]
        else:
            num -= len(self.provider.ips)
            self.provider.ips.extend(self.provider.get_ips(num))
            return self.provider.ips

