'''
Created on Jun 15, 2015

@author: lubo
'''
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object
from .cache import PrecomputeStore
from django.conf import settings


class Precompute(object):

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self, data):
        raise NotImplementedError()

    def is_precomputed(self):
        raise NotImplementedError()

    def precompute(self):
        raise NotImplementedError()


class PrecomputeRegister(object):

    def __init__(self, register={}):
        self.store = PrecomputeStore()
        self.reg = {}
        self.preload_active = getattr(
            settings,
            "PRELOAD_ACTIVE",
            False)

        for key, precompute in register.items():
            self.register(key, precompute)

    def register(self, key, precompute):
        assert isinstance(precompute, Precompute)

        if key in self.reg:
            raise KeyError("precompute object <%s> already registered" % key)

        self.reg[key] = precompute
        if not self.preload_active:
            return

        self._load_or_compute(key, precompute)

    def _load_or_compute(self, key, precompute):
        data = self.store.retrieve(key)
        print("trying to find precomputed {}".format(key))
        if data:
            print("precomputed {} found... loading...".format(key))
            precompute.deserialize(data)
        else:
            print("precomputed {} NOT found... computing...".format(key))
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)

    def recompute(self):
        for key, precompute in self.reg.items():
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)

    def get(self, key):
        assert key in self.reg, \
            [key, list(self.reg.keys())]
        precompute = self.reg[key]
        if not precompute.is_precomputed():
            self._load_or_compute(key, precompute)

        return precompute

    def __contains__(self, item):
        return item in self.reg

    def keys(self):
        return list(self.reg.keys())


_REGISTER = PrecomputeRegister()


def get_register():
    # global _REGISTER
    return _REGISTER


def register(key, precompute):
    # global _REGISTER
    _REGISTER.register(key, precompute)


def get(key):
    # global _REGISTER

    try:
        value = _REGISTER.get(key)
    finally:
        pass

    return value


def has_data(key):
    # global _REGISTER
    value = False

    try:
        value = key in _REGISTER  # @IgnorePep8
    finally:
        pass

    return value
