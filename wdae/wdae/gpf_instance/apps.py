"""Provides class for configuing WDAE Django application."""
import logging

from django.apps import AppConfig
from django.conf import settings

from gpf_instance.gpf_instance import WGPFInstance, get_wgpf_instance

logger = logging.getLogger(__name__)


class WDAEConfig(AppConfig):
    """Configure WDAE django application."""

    name = "gpf_instance"

    @staticmethod
    def load_extensions(gpf_instance: WGPFInstance) -> None:
        """Load WDAE GPF instance extensions."""
        # pylint: disable=import-outside-toplevel
        logger.info("Loading extensions")
        from importlib.metadata import entry_points
        discovered_entries = entry_points(group="wdae.gpf_instance.extensions")
        for entry in discovered_entries:
            extension_loader = entry.load()
            extension_loader(gpf_instance)

    def ready(self) -> None:
        logger.info("WGPConfig application starting...")
        AppConfig.ready(self)

        config_filepath = getattr(settings, "GPF_INSTANCE_CONFIG_PATH", None)

        logger.info("GPF instance config: %s", config_filepath)

        gpf_instance = get_wgpf_instance(config_filepath)
        if gpf_instance is None:
            logger.warning("GPF instance is not loaded")
            return

        if not settings.STUDIES_EAGER_LOADING:
            logger.info("skip preloading gpf instance...")
            self.load_extensions(gpf_instance)
            return

        for phenotype_data_id in gpf_instance.get_phenotype_data_ids():
            phenotype_data = gpf_instance.get_phenotype_data(phenotype_data_id)
            if phenotype_data._browser is not None \
                and phenotype_data.is_browser_outdated(phenotype_data._browser):  # noqa: SLF001
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
        self.load_extensions(gpf_instance)
