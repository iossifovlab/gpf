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
        self.reg = {}
        for key, precompute in register.items():
            self.register(key, precompute)
        
    def register(self, key, precompute):
        if key in self.reg:
            raise KeyError("precompute object <%s> already registered" % key)
        
        data = self.store.retrieve(key)
        if data:
            precompute.deserialize(data)
        else:
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)
        
        self.reg[key] = precompute
        
    
    def recompute(self):
        for key, precompute in self.register.items():
            precompute.precompute()
            data = precompute.serialize()
            self.store.store(key, data)
    
    def get(self, key):
        return self.reg[key]
    
    def keys(self):
        return self.reg.keys()
    


_REGISTER = PrecomputeRegister()

def get_register():
    global _REGISTER
    return _REGISTER

def register(key, precompute):
    global _REGISTER
    print("register keys: %s" % _REGISTER.reg.keys())
    _REGISTER.register(key, precompute)

def get(key):
    global _REGISTER
    print("keys: %s" % _REGISTER.reg.keys())
    print("reg: %s" % _REGISTER.reg)

    try:
        value = _REGISTER.get(key)
    finally:
        pass
    
    print("value: %s" % value)
    return value
    