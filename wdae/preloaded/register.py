'''
Created on Nov 5, 2015

@author: lubo
'''
from django.conf import settings


class Preload(object):

    def load(self):
        raise NotImplementedError()

    def is_loaded(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()


_REGISTER = {}


def get_register():
    global _REGISTER
    return _REGISTER


def register(key, preload):
    assert isinstance(preload, Preload)

    preload_active = getattr(
        settings,
        "PRELOAD_ACTIVE",
        False)

    if preload_active:
        preload.load()

    global _REGISTER
    _REGISTER[key] = preload


def get(key):
    global _REGISTER

    try:
        preload = _REGISTER.get(key)
        if not preload.is_loaded():
            preload.load()
        return preload.get()
    finally:
        pass

    return None


def has_key(key):
    global _REGISTER
    value = False

    try:
        value = _REGISTER.has_key(key)  # @IgnorePep8
    finally:
        pass

    return value
