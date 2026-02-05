from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AttributeDesc,
)
from dae.genomic_resources.aggregators import build_aggregator
from dae.genomic_resources.genomic_scores import CnvCollection


def build_cnv_collection_annotator(pipeline: AnnotationPipeline,
                                   info: AnnotatorInfo) -> Annotator:
    return CnvCollectionAnnotator(pipeline, info)


class CnvCollectionAnnotator(Annotator):
    """Simple effect annotator class."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):

        cnv_collection_resrouce_id = info.parameters.get("resource_id")
        if cnv_collection_resrouce_id is None:
            raise ValueError(f"Can't create {info.type}: "
                             "no resrouce_id parameter.")
        resource = pipeline.repository.get_resource(cnv_collection_resrouce_id)
        self.cnv_collection = CnvCollection(resource)
        info.resources.append(resource)

        self.cnv_filter = None
        cnv_filter_str = info.parameters.get("cnv_filter")
        if cnv_filter_str is not None:
            try:
                # pylint: disable=eval-used
                self.cnv_filter = eval(  # noqa: S307
                    f"lambda cnv: { cnv_filter_str }")
            except Exception as error:
                raise ValueError(
                    f"The cnv_filter |{cnv_filter_str}| is "
                    f"sytactically invalid.", error) from error

        if not info.attributes:
            info.attributes = [AttributeInfo(
                "count", "count",
                internal=False, parameters={})]

        self.cnv_attributes = {}
        all_attributes = self.get_all_attribute_descriptions()
        for attribute_def in info.attributes:
            if attribute_def.source not in all_attributes:
                raise ValueError(f"The source {attribute_def.source} "
                                 " is not supported for the annotator "
                                 f"{info.type}")

            attribute = all_attributes[attribute_def.source]
            if attribute_def.source.startswith("attribute."):
                attribute_name = attribute_def.source[len("attribute."):]
                res_attribute_def = self.cnv_collection\
                    .get_score_definition(attribute_name)
                assert res_attribute_def is not None
                if "aggregator" in attribute_def.parameters:
                    aggregator = attribute_def.parameters["aggregator"]
                else:
                    aggregator = attribute.params["aggregator"]
                attribute_def.type = attribute.type
                attribute_def.description = attribute.description
                attribute_def._documentation = f"""
                    {attribute_def.description}

                    small values: {res_attribute_def.small_values_desc},
                    large_values: {res_attribute_def.large_values_desc}
                    aggregator: {aggregator}
                """  # noqa: SLF001

                self.cnv_attributes[attribute_def.name] = \
                    (attribute, aggregator)
            else:
                attribute_def.type = attribute.type
                attribute_def.description = attribute.description

        super().__init__(pipeline, info)

    def get_all_attribute_descriptions(self) -> dict[str, AttributeDesc]:
        attributes = {
            "count": AttributeDesc(
                name="count",
                type="int",
                description="The number of CNVs overlapping with the "
                "annotatable.",
            ),
        }
        for score_id, score_def in \
                self.cnv_collection.score_definitions.items():
            score_id = f"attribute.{score_id}"
            attributes[score_id] = AttributeDesc(
                name=score_id,
                type=score_def.value_type,
                description=score_def.desc,
                params={"aggregator": score_def.allele_aggregator},
            )
        return attributes

    def open(self) -> Annotator:
        self.cnv_collection.open()
        return super().open()

    def close(self) -> None:
        self.cnv_collection.close()
        super().close()

    def annotate(
        self, annotatable: Annotatable | None,
        context: dict[str, Any],  # noqa: ARG002
    ) -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()

        cnvs = self.cnv_collection.fetch_cnvs(
            annotatable.chrom, annotatable.pos, annotatable.pos_end)

        if self.cnv_filter:
            cnvs = [cnv for cnv in cnvs if self.cnv_filter(cnv)]

        aggregators = {name: build_aggregator(aggregator)
                       for name, (_, aggregator)
                       in self.cnv_attributes.items()}

        for cnv in cnvs:
            for name, (attribute, _) in self.cnv_attributes.items():
                attribute_name = attribute.name[len("attribute."):]
                aggregators[name].add(cnv.attributes[attribute_name])

        ret = {}
        for attribute_config in self._info.attributes:
            if attribute_config.name in self.cnv_attributes:
                ret[attribute_config.name] = \
                    aggregators[attribute_config.name].get_final()
            elif attribute_config.source == "count":
                ret[attribute_config.name] = len(cnvs)

        return ret
