from typing import Any, Optional
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotation_pipeline import AttributeInfo
from dae.annotation.annotation_pipeline import Annotator
from dae.annotation.annotation_pipeline import AnnotatorInfo
from dae.genomic_resources.aggregators import build_aggregator
from dae.genomic_resources.cnv_collection import CnvCollection


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
                self.cnv_filter = eval(f"lambda cnv: { cnv_filter_str }")
            except Exception as error:
                raise ValueError(
                    f"The cnv_filter |{cnv_filter_str}| is "
                    f"sytactically invalid.", error) from error

        if not info.attributes:
            info.attributes = [AttributeInfo("count", "count", False, {})]

        source_type_desc = {
            "count": ("int", "The number of CNVs overlapping with "
                      "the annotatable.")
        }

        self.cnv_attributes = {}
        for attribute_def in info.attributes:
            if attribute_def.source.startswith("attribute."):
                attribute = attribute_def.source[len("attribute."):]
                if attribute not in self.cnv_collection.score_defs:
                    raise ValueError(f"The attribute {attribute} is not "
                                     "supported for the cnvs in the"
                                     "cnv_collection "
                                     f"{cnv_collection_resrouce_id}")
                res_attribute_def = self.cnv_collection.score_defs[attribute]
                if "aggregator" in attribute_def.parameters:
                    aggregator = attribute_def.parameters["aggregator"]
                else:
                    aggregator = res_attribute_def.allele_aggregator
                attribute_def.type = res_attribute_def.value_type
                attribute_def.description = res_attribute_def.desc
                attribute_def._documentation = f"""
                    {attribute_def.description}

                    small values: {res_attribute_def.small_values_desc},
                    large_values: {res_attribute_def.large_values_desc}
                    aggregator: {aggregator}
                """

                self.cnv_attributes[attribute_def.name] = \
                    (attribute, aggregator)
            elif attribute_def.source in source_type_desc:
                att_type, att_desc = source_type_desc[attribute_def.source]
                attribute_def.type = att_type
                attribute_def.description = att_desc
            else:
                raise ValueError(f"The source {attribute_def.source} "
                                 " is not supported for the annotator "
                                 f"{info.type}")

        super().__init__(pipeline, info)

    def open(self) -> Annotator:
        self.cnv_collection.open()
        return super().open()

    def close(self) -> None:
        self.cnv_collection.close()
        super().close()

    def annotate(
        self, annotatable: Optional[Annotatable], _: dict[str, Any]
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
                aggregators[name].add(cnv.attributes[attribute])

        ret = {}
        for attribute_config in self._info.attributes:
            if attribute_config.name in self.cnv_attributes:
                ret[attribute_config.name] = \
                    aggregators[attribute_config.name].get_final()
            elif attribute_config.source == "count":
                ret[attribute_config.name] = len(cnvs)

        return ret
