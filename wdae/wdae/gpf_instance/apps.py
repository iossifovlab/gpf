"""Provides class for configuing WDAE Django application."""
import logging
import pathlib

from django.apps import AppConfig
from django.conf import settings

from gpf_instance.gpf_instance import get_wgpf_instance

logger = logging.getLogger(__name__)


class WDAEConfig(AppConfig):
    """Configure WDAE django application."""

    name = "gpf_instance"

    def ready(self) -> None:
        logger.warning("WGPConfig application starting...")
        AppConfig.ready(self)
        config_filename = None
        if getattr(settings, "GPF_INSTANCE_CONFIG", None):
            config_filename = pathlib.Path(__file__).parent.joinpath(
                settings.GPF_INSTANCE_CONFIG)

            logger.error("GPF instance config: %s", config_filename)

        gpf_instance = get_wgpf_instance(config_filename)

        if not settings.STUDIES_EAGER_LOADING:
            logger.info("skip preloading gpf instance...")
            return

        try:
            logger.warning("eager loading of GPF instance and studies")
            gpf_instance.load()
            result = gpf_instance.get_all_genotype_data()
            logger.info("preloading studies: %s", result)

            gpf_instance.prepare_agp_configuration()

        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem while eager loading of studies", exc_info=True)
        logger.warning("Eager loading DONE")
