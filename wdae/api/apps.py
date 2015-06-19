'''
Created on Jun 16, 2015

@author: lubo
'''

from django.apps import AppConfig
from django.conf import settings

from api.precompute.register import get_register
from importlib import import_module

# from api.enrichment.background import SynonymousBackground
# from api.precompute.precompute import PrecomputeDenovoGeneSets 




class WdaeApiConfig(AppConfig):
    name = "api"
    
    def _split_class_name(self, cls_name):
        spl = cls_name.split('.')
        m = '.'.join(spl[:-1])
        [c] = spl[-1:]
        
        return m,c
            
    def ready(self):
        AppConfig.ready(self)
        
        register = get_register()
        for key, cls_name in settings.PRECOMPUTE_CONFIG.items():
            m,c = self._split_class_name(cls_name)
            module = import_module(m)
            cls = getattr(module, c)
            register.register(key, cls())
        
        
            
