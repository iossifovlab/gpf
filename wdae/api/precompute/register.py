'''
Created on Jun 15, 2015

@author: lubo
'''
from api.precompute.cache import PrecomputeStore

class Precompute(object):
    
    def serialize(self):
        raise NotImplemented()
    
    def deserialize(self, data):
        raise NotImplemented()

    def precompute(self):
        raise NotImplemented()
    

class PrecomputeRegister(object):

    def __init__(self, register={}):
        self.store = PrecomputeStore()
        self.register = {}
        for key, precompute in register.items():
            self.register[key] = precompute
        
    def register(self, key, precompute):
        if key in self.register:
            raise KeyError("precompute object <%s> already registered" % key)
        
        data = self.store.retrieve(key)
        if data:
            precompute.deserialize(data)
        else:
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)
        
        self.register[key] = precompute
        
    
    def recompute(self):
        for key, precompute in self.register.items():
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)
    
    def get(self, key):
        return self.register[key]