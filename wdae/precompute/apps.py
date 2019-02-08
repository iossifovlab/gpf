'''
Created on Jun 16, 2015

@author: lubo
'''
from __future__ import unicode_literals

from django.apps import AppConfig
from django.conf import settings

from importlib import import_module
# from DAE import pheno
# from pheno_browser_api.common import PhenoBrowserCommon
# from common.progress import red_print
import logging


logger = logging.getLogger(__name__)


class WdaePrecomputeConfig(AppConfig):
    name = "precompute"
    loaded = False

    def _split_class_name(self, cls_name):
        spl = cls_name.split('.')
        m = '.'.join(spl[:-1])
        [c] = spl[-1:]

        return m, c

    def _load_precomputed(self):
        from precompute.register import get_register
        register = get_register()
        for key, cls_name in list(settings.PRECOMPUTE_CONFIG.items()):
            m, c = self._split_class_name(cls_name)
            module = import_module(m)
            cls = getattr(module, c)
            register.register(key, cls())

    def _load_preloaded(self):
        from preloaded.register import register
        for key, cls_name in list(settings.PRELOAD_CONFIG.items()):
            m, c = self._split_class_name(cls_name)
            logger.info("preloading  {}.{}".format(m, c))
            module = import_module(m)
            cls = getattr(module, c)
            preload = cls()
            register(key, preload)
        logger.warn("PRELOADING DONE!!!")

    def _check_pheno_browser_api_cache(self):
        # pheno_db_names = pheno.get_pheno_db_names()
        # for dbname in pheno_db_names:
        #     if PhenoBrowserCommon.should_recompute(dbname):
        #         red_print(
        #             ">>> WARNING: "
        #             "phenotype DB <{}> browser cache needs recomputing"
        #             " Please call: ./manage.py pheno_browser_cache".format(
        #                 dbname)
        #         )
        pass

    def ready(self):
        logger.warn("WdaePrecomputeConfig.read() started...")
        super(WdaePrecomputeConfig, self).ready()
        if not self.loaded:
            self._check_pheno_browser_api_cache()
            self._load_preloaded()
            self._load_precomputed()
            self.loaded = True
