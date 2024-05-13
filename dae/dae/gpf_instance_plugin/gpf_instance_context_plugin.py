import logging
from typing import Any, Optional

from dae.genomic_resources.genomic_context import (
    GC_GENE_MODELS_KEY,
    GC_GRR_KEY,
    GC_REFERENCE_GENOME_KEY,
    GenomicContext,
    SimpleGenomicContextProvider,
    register_context_provider,
)

logger = logging.getLogger(__name__)


class GPFInstanceGenomicContext(GenomicContext):
    """Defines GPFInstance genomic context."""

    def __init__(self, gpf_instance: Any) -> None:
        # pylint: disable=import-outside-toplevel
        from dae.gpf_instance.gpf_instance import GPFInstance
        if not isinstance(gpf_instance, GPFInstance):
            raise TypeError(
                f"invalid gpf instance type: {type(gpf_instance)}")

        self.gpf_instance = gpf_instance

    def get_context_object(self, key: str) -> Optional[Any]:
        if key == GC_GENE_MODELS_KEY:
            return self.gpf_instance.gene_models
        if key == GC_REFERENCE_GENOME_KEY:
            return self.gpf_instance.reference_genome
        if key == GC_GRR_KEY:
            return self.gpf_instance.grr
        if key == "annotation_pipeline":
            return self.gpf_instance.get_annotation_pipeline()
        if key == "gpf_instance":
            return self.gpf_instance
        logger.info(
            "can't find %s in GPF instance genomic context", key)
        return None

    def get_context_keys(self) -> set[str]:
        return {
            GC_GENE_MODELS_KEY, GC_REFERENCE_GENOME_KEY,
            GC_GRR_KEY, "annotation_pipeline", "gpf_instance",
        }

    def get_source(self) -> tuple[str, ...]:
        return ("gpf_instance", self.gpf_instance.dae_dir)


class GPFInstanceGenomicContextProvider(SimpleGenomicContextProvider):
    """Defines GPFInstance genomic context provider."""

    @staticmethod
    def context_builder() -> Optional[GenomicContext]:
        """Build GPF instance genomic context."""
        try:
            # pylint: disable=import-outside-toplevel
            from dae.gpf_instance.gpf_instance import GPFInstance
            return GPFInstanceGenomicContext(GPFInstance.build())
        except Exception as ex:  # noqa pylint: disable=broad-except
            logger.info(
                "unable to create default gpf instance context: %s", ex)
            return None

    def __init__(self) -> None:
        super().__init__(
            GPFInstanceGenomicContextProvider.context_builder,
            "GPFInstanceProvider",
            100)


def init_gpf_instance_genomic_context_plugin() -> None:
    register_context_provider(GPFInstanceGenomicContextProvider())


def init_test_gpf_instance_genomic_context_plugin(
    gpf_instance: Any,
) -> None:
    """Init GPF instance genomic context plugin for testing."""
    # pylint: disable=import-outside-toplevel
    from dae.gpf_instance.gpf_instance import GPFInstance
    if not isinstance(gpf_instance, GPFInstance):
        raise TypeError(f"invalid gpf instance type: {type(gpf_instance)}")

    class GPFInstanceContextProvider(SimpleGenomicContextProvider):
        """Defines GPFInstance genomic context provider."""

        @staticmethod
        def context_builder() -> Optional[GenomicContext]:
            """Build GPF instance genomic context."""
            try:
                return GPFInstanceGenomicContext(gpf_instance)
            except Exception as ex:  # noqa pylint: disable=broad-except
                logger.info(
                    "unable to create default gpf instance context: %s", ex)
                return None

        def __init__(self) -> None:
            super().__init__(
                GPFInstanceContextProvider.context_builder,
                "GPFInstanceProvider",
                10)

    register_context_provider(GPFInstanceContextProvider())
