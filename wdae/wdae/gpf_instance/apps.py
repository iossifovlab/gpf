import logging

from django.apps import AppConfig
from django.conf import settings

from gpf_instance.gpf_instance import load_gpf_instance

logger = logging.getLogger(__name__)


class EagerLoadingConfig(AppConfig):
    name = "gpf_instance"

    def ready(self):
        logger.warn("EagerLoadingConfig.read() started...")
        AppConfig.ready(self)
        if settings.STUDIES_EAGER_LOADING:
            try:
                logger.warn(
                    "STUDIES EAGER LOADING: going to call load_gpf_instance()...")
                gpf_instance = load_gpf_instance()
                result = gpf_instance.get_all_genotype_data()
                logger.info(result)
            except Exception as ex:
                logger.error(f"problem while eager loading of studies; {ex}")
                logger.exception(ex)
