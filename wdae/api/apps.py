'''
Created on Jun 16, 2015

@author: lubo
'''

from django.apps import AppConfig
from django.conf import settings

from importlib import import_module


class WdaeApiConfig(AppConfig):
    name = "api"

    def _split_class_name(self, cls_name):
        spl = cls_name.split('.')
        m = '.'.join(spl[:-1])
        [c] = spl[-1:]

        return m, c

    def _load_precomputed(self):
        from api.precompute.register import get_register
        register = get_register()
        for key, cls_name in settings.PRECOMPUTE_CONFIG.items():
            m, c = self._split_class_name(cls_name)
            module = import_module(m)
            cls = getattr(module, c)
            register.register(key, cls())

    def _load_preloaded(self):
        from api.preloaded.register import get_register
        register = get_register()
        for key, cls_name in settings.PRELOAD_CONFIG.items():
            m, c = self._split_class_name(cls_name)
            module = import_module(m)
            cls = getattr(module, c)
            preload = cls()
            preload.load()
            register[key] = preload.get()

    def ready(self):
        AppConfig.ready(self)
        self._load_precomputed()
        self._load_preloaded()
