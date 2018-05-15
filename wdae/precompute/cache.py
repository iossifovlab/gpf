'''
Created on Jun 10, 2015

@author: lubo
'''
import hashlib

from django.core.cache import caches
from datetime import datetime

from helpers.logger import LOGGER


class PrecomputeStore(object):

    MAX_CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self):
        self.cache = caches['pre']

    def hash_key(self, key):
        assert isinstance(key, str), type(key)
        key = bytearray(key, 'utf-8')
        return hashlib.sha1(key).hexdigest()

    def store(self, key, data):
        assert isinstance(key, str)
        for v in data.values():
            assert isinstance(v, bytes), type(v)
            assert (len(v) < self.MAX_CHUNK_SIZE)

        description = {"name": key,
                       "keys": list(data.keys()),
                       "timestamp": datetime.now()}

        LOGGER.info("storing cache value: for %s at %s" %
                    (description['name'],
                     description['timestamp'],))

        values = {"{}.{}".format(key, k): v for k, v in data.items()}
        values["{}.description".format(key)] = description

        v = {
            self.hash_key(k): v
            for k, v in values.items()
        }
        print(v, type(v))
        self.cache.set_many(v)

    def retrieve(self, key):
        dkey = self.hash_key("{}.description".format(key))
        description = self.cache.get(dkey)
        if not description:
            return None

        vkeys = {self.hash_key("{}.{}".format(key, k)): k
                 for k in description['keys']}
        result = self.cache.get_many(vkeys.keys())

        return {vkeys[k]: v for k, v in result.items()}
