#!/usr/bin/env python


"""
@PROJECT: RPC_twisted
@AUTHOR: momen
@TIME: 2/13/20 5:08 PM
"""


import importlib


def load_object(name, default=None):
    module, obj_cls = name.rsplit('.', 1)
    module = importlib.import_module(module)
    obj_cls = getattr(module, obj_cls, default)
    if not obj_cls:
        obj_cls = importlib.import_module(name)
    return obj_cls
