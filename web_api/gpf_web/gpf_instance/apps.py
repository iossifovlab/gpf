"""Provides class for configuing WDAE Django application."""
import logging
import sys

from django.apps import AppConfig
from django.conf import settings

from gpf_instance.gpf_instance import (
    ensure_dataset_hierarchy,
    get_wgpf_instance,
)

logger = logging.getLogger(__name__)


class WDAEConfig(AppConfig):
    """Configure WDAE django application."""

    name = "gpf_instance"

    def ready(self) -> None:
        super().ready()
        logger.info("WDAEConfig application started with: %s", sys.argv)

        is_runserver = any(arg.casefold() == "runserver" for arg in sys.argv)
        is_gunicorn = any("gunicorn" in arg.casefold() for arg in sys.argv)
        if not is_runserver and not is_gunicorn:
            return

        logger.info("WDAEConfig application starting...")
        config_filepath = getattr(settings, "GPF_INSTANCE_CONFIG_PATH", None)

        logger.info("GPF instance config: %s", config_filepath)

        gpf_instance = get_wgpf_instance(config_filepath)
        if gpf_instance is None:
            logger.warning("GPF instance is not loaded")
            return

        # Boot-time safety net for the dataset-permission hierarchy
        # (iossifovlab/gpf#925): with the lazy first-request rebuild removed
        # from QueryBaseView, build the hierarchy once here if it is missing
        # so a worker never serves against an empty DatasetHierarchy (which
        # would deny every user).  This is a correctness requirement, NOT a
        # perf optimization -- it must run even when STUDIES_EAGER_LOADING is
        # off, so it is placed before that early-return.  It is off the
        # request hot path and self-healing; the emptiness guard means only
        # the first worker pays the rebuild.  The migrate/runserver gating
        # above guarantees the tables already exist.
        if ensure_dataset_hierarchy(gpf_instance):
            logger.info("dataset-permission hierarchy built at boot")

        if not settings.STUDIES_EAGER_LOADING:
            logger.info("skip preloading gpf instance...")
            return

        for phenotype_data_id in gpf_instance.get_phenotype_data_ids():
            phenotype_data = gpf_instance.get_phenotype_data(phenotype_data_id)
            if (phenotype_data._browser is not None  # noqa: SLF001
                    and phenotype_data.is_browser_outdated(
                    phenotype_data._browser)):  # noqa: SLF001
                logger.warning(
                    "phenotype_data %s browser is outdated",
                    phenotype_data_id,
                )
        try:
            logger.info("eager loading of GPF instance and studies")
            gpf_instance.load()
            pheno = gpf_instance.get_all_phenotype_data()
            logger.info("preloading phenotype studies: %s", pheno)

            geno = gpf_instance.get_all_genotype_data()
            logger.info("preloading genotype studies: %s", geno)

            gpf_instance.prepare_gp_configuration()

        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "problem while eager loading of studies")
        logger.info("Eager loading DONE")
