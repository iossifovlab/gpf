from __future__ import annotations

import logging

from dae.annotation.annotation_pipeline import AnnotationPipeline, AttributeInfo
from dae.effect_annotation.effect import AlleleEffects
from dae.variants_loaders.raw.loader import (
    FullVariantsIterator,
    VariantsLoader,
    VariantsLoaderDecorator,
)

logger = logging.getLogger(__name__)


class AnnotationPipelineDecorator(VariantsLoaderDecorator):
    """Annotate variants by processing them through an annotation pipeline."""

    def __init__(
        self, variants_loader: VariantsLoader,
        annotation_pipeline: AnnotationPipeline,
    ) -> None:
        super().__init__(variants_loader)

        self.annotation_pipeline = annotation_pipeline
        logger.debug(
            "creating annotation pipeline decorator with "
            "annotation pipeline: %s", annotation_pipeline.get_attributes())

        self.set_attribute("annotation_schema", self.annotation_schema)
        self.set_attribute(
            "extra_attributes",
            variants_loader.get_attribute("extra_attributes"),
        )

    @property
    def annotation_schema(self) -> list[AttributeInfo]:
        return self.annotation_pipeline.get_attributes()

    def full_variants_iterator(
        self,
    ) -> FullVariantsIterator:
        with self.annotation_pipeline.open() as annotation_pipeline:
            internal_attributes = {
                attr.name for attr in self.annotation_pipeline.get_attributes()
                if attr.internal
            }

            for (summary_variant, family_variants) in \
                    self.variants_loader.full_variants_iterator():
                for sallele in summary_variant.alt_alleles:
                    attributes = annotation_pipeline.annotate(
                        sallele.get_annotatable())
                    if "allele_effects" in attributes:
                        allele_effects = attributes["allele_effects"]
                        assert isinstance(allele_effects, AlleleEffects), \
                            attributes
                        # pylint: disable=protected-access
                        sallele._effects = allele_effects  # noqa: SLF001
                        del attributes["allele_effects"]
                    public_attributes = {
                        key: value for key, value in attributes.items()
                        if key not in internal_attributes
                    }
                    sallele.update_attributes(public_attributes)
                yield summary_variant, family_variants

    def close(self) -> None:
        self.annotation_pipeline.close()
