'''
Created on Nov 5, 2015

@author: lubo
'''


class Preload(object):

    def load(self):
        raise NotImplemented

    def get(self):
        raise NotImplemented


_REGISTER = {}


def get_register():
    global _REGISTER
    return _REGISTER


def register(key, preload):
    global _REGISTER
    _REGISTER[key] = preload


def get(key):
    global _REGISTER

    try:
        value = _REGISTER.get(key)
    finally:
        pass

    return value


def has_key(key):
    global _REGISTER
    value = False

    try:
        value = _REGISTER.has_key(key)  # @IgnorePep8
    finally:
        pass

    return value
