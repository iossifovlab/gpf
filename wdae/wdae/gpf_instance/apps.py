"""Provides class for configuing WDAE Django application."""
import logging
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings

from gpf_instance.gpf_instance import load_gpf_instance

logger = logging.getLogger(__name__)


class WDAEConfig(AppConfig):
    """Configure WDAE django application."""

    name = "gpf_instance"

    def ready(self):
        logger.warning("WGPConfig application starting...")

        AppConfig.ready(self)
        config_filename = None
        if getattr(settings, "GPF_INSTANCE_CONFIG", None):
            config_filename = Path(__file__).parent.joinpath(
                settings.GPF_INSTANCE_CONFIG)

            logger.error("GPF instance config: %s", config_filename)

        if not settings.STUDIES_EAGER_LOADING:
            load_gpf_instance(config_filename)
            logger.info("skip preloading gpf instance...")
            return

        try:
            logger.warning(
                "calling load_gpf_instance with STUDIES_EAGER_LOADING=True")
            gpf_instance = load_gpf_instance(config_filename)
            gpf_instance.load()
            result = gpf_instance.get_all_genotype_data()
            logger.info("preloading studies: %s", result)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem while eager loading of studies", exc_info=True)
        logger.warning("Eager loading DONE")
