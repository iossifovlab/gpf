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
        work_dir = None
        eager_loading = False

        if getattr(settings, "TESTING", None):
            work_dir = Path(__file__).parents[3].joinpath(
                "data/data-hg19-local")

            print(100 * "+")
            logger.error("testing environment... work_dir: %s", work_dir)
            print(100 * "+")

        if settings.STUDIES_EAGER_LOADING:
            logger.warning("Eager loading started")

        if not work_dir and not eager_loading:
            logger.info("skip preloading gpf instance...")
            return

        try:
            logger.warning(
                "going to call load_gpf_instance with "
                "work_dir=%s; eager_loading=%s", work_dir, eager_loading)
            gpf_instance = load_gpf_instance(work_dir=work_dir)
            if eager_loading:
                result = gpf_instance.get_all_genotype_data()
                logger.info(result)
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "problem while eager loading of studies", exc_info=True)
        logger.warning("Eager loading DONE")
