'''
Created on Jun 10, 2015

@author: lubo
'''
import hashlib

from django.core.cache import caches
from datetime import datetime


class PrecomputeStore(object):

    MAX_CHUNK_SIZE = 1024*1024
    def __init__(self):
        self.cache = caches['pre']
        
    def hash_key(self, key):
        return hashlib.sha1(key).hexdigest()
    
    
    def store(self, key, data):
        for v in data.values():
            assert isinstance(v, str)
            assert (len(v) < self.MAX_CHUNK_SIZE)

        description = {"name": key,
                       "keys": data.keys(),
                       "timestamp": datetime.now()}
        
        values = {"{}.{}".format(key, k):v for k,v in data.items()}
        values ["{}.description".format(key)] = description
        
        self.cache.set_many({self.hash_key(k): v for k,v in values.items()})
    
    
    def retrieve(self, key):
        dkey = self.hash_key("{}.description".format(key))
        description = self.cache.get(dkey)
        
        
        vkeys = {self.hash_key("{}.{}".format(key, k)): k
                 for k in description['keys']}
        result = self.cache.get_many(vkeys.keys())
        
        return {vkeys[k]: v for k,v in result.items()}