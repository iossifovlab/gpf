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

        AppConfig.ready(self)
        eager_loading = False

        if settings.STUDIES_EAGER_LOADING:
            logger.warning("Eager loading started")

        if not eager_loading:
            logger.info("skip preloading gpf instance...")
            return

        try:
            logger.warning(
                "going to call load_gpf_instance with "
                "eager_loading=%s", eager_loading)
            gpf_instance = load_gpf_instance()
            result = gpf_instance.get_all_genotype_data()
            logger.info("preloading studies: %s", result)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem while eager loading of studies", exc_info=True)
        logger.warning("Eager loading DONE")


class WDAETestingConfig(AppConfig):
    """Configure WDAE django application."""

    name = "gpf_instance"

    def ready(self):

        AppConfig.ready(self)
        config_filename = None

        if getattr(settings, "TESTING", None):
            config_filename = Path(__file__).parents[3].joinpath(
                "data/data-hg19-local/gpf_instance.yaml")

            logger.error("testing environment... config: %s", config_filename)

        try:
            logger.warning(
                "going to call load_gpf_instance with %s",
                config_filename)
            load_gpf_instance(config_filename)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem while preloading testing gpf instance",
                exc_info=True)
        logger.warning("preloading testing gpf instance done")
