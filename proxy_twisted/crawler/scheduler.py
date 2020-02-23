#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 2/21/20 10:35 PM
"""

from queue import Queue


import logging

logger = logging.getLogger(__name__)


class Scheduler(object):
    def __init__(self, engine, settings):
        self.queue = Queue()

    @classmethod
    def produce(cls, engine, settings):
        return cls(engine, settings)

    def dequeue_request(self, block=False, timeout=0):
        return self.queue.get(block=block, timeout=timeout)

    def enqueue_request(self, request, block=False, timeout=0):
        return self.queue.put(request, block=block, timeout=timeout)

