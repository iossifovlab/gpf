import textwrap
from collections.abc import Callable
from typing import Any

from lark import Lark, Token, Tree

from gain.annotation.annotatable import Annotatable
from gain.annotation.annotation_config import (
    AnnotationConfigurationError,
    AnnotatorInfo,
    AttributeInfo,
)
from gain.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    AttributeDesc,
)
from gain.genomic_resources.aggregators import build_aggregator
from gain.genomic_resources.genomic_scores import CNV, CnvCollection


def build_cnv_collection_annotator(pipeline: AnnotationPipeline,
                                   info: AnnotatorInfo) -> Annotator:
    return CnvCollectionAnnotator(pipeline, info)


class CnvCollectionAnnotator(Annotator):
    """Simple effect annotator class."""

    CNV_FILTER_GRAMMAR = textwrap.dedent("""
        ?start: filter | and_ | or

        and_: filter "and" filter

        or: filter "or" filter

        ?filter: subject operator subject | or | and_

        ?subject: variable | value

        value: "\\"" word "\\"" | number

        variable: word

        operator: equals | greater_than | less_than | in

        equals: "=="

        greater_than: ">"

        less_than: "<"

        in: "in"

        word: /[a-zA-Z!@#$%^&*()_+]+/

        number: /[0-9\\.]+/

        %ignore " "
    """)

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        cnv_collection_resrouce_id = info.parameters.get("resource_id")
        if cnv_collection_resrouce_id is None:
            raise ValueError(f"Can't create {info.type}: "
                             "no resrouce_id parameter.")
        resource = pipeline.repository.get_resource(cnv_collection_resrouce_id)
        self.cnv_collection = CnvCollection(resource)
        info.resources.append(resource)

        self.filter_parser = Lark(self.CNV_FILTER_GRAMMAR)

        self.cnv_filter = None
        cnv_filter_str = info.parameters.get("cnv_filter")
        if cnv_filter_str is not None:
            assert isinstance(cnv_filter_str, str)

            cnv_filter_str = cnv_filter_str.replace(
                "\n", " ").replace("\t", " ").strip()
            try:
                self.cnv_filter = self._build_cnv_filter_func(
                    self.filter_parser.parse(cnv_filter_str))
            except Exception as e:
                raise AnnotationConfigurationError(
                    f"Error parsing cnv_filter: {e}") from e

        all_attributes = self.get_all_attribute_descriptions()

        if not info.attributes:
            for attr in all_attributes.values():
                info.attributes.append(AttributeInfo(
                    attr.name or attr.source, attr.source,
                    internal=attr.internal, parameters=attr.params,
                    _type=attr.type, description=attr.description,
                    attribute_type=attr.attribute_type))
            info.attributes = [AttributeInfo(
                "count", "count",
                internal=False, parameters={})]

        self.cnv_attributes = {}
        for attribute_def in info.attributes:
            if attribute_def.source not in all_attributes:
                raise ValueError(f"The source {attribute_def.source} "
                                 " is not supported for the annotator "
                                 f"{info.type}")

            attribute = all_attributes[attribute_def.source]
            attribute_name = attribute_def.source
            if "aggregator" in attribute_def.parameters:
                aggregator = attribute_def.parameters["aggregator"]
            else:
                aggregator = attribute.params.get("aggregator")
            attribute_def.value_type = attribute.type
            attribute_def.description = attribute.description
            res_attribute_def = self.cnv_collection\
                .get_score_definition(attribute_name)
            if res_attribute_def is not None:
                attribute_def._documentation = f"""
                    {attribute_def.description}

                    small values: {res_attribute_def.small_values_desc},
                    large_values: {res_attribute_def.large_values_desc}
                    aggregator: {aggregator}
                """  # noqa: SLF001

            self.cnv_attributes[attribute_def.name] = \
                (attribute, aggregator)

        super().__init__(pipeline, info)

    def get_all_attribute_descriptions(self) -> dict[str, AttributeDesc]:
        attributes = {
            "count": AttributeDesc(
                source="count",
                type="int",
                description="The number of CNVs overlapping with the "
                "annotatable.",
            ),
        }
        for score_id, score_def in \
                self.cnv_collection.score_definitions.items():
            attributes[score_id] = AttributeDesc(
                source=score_id,
                type=score_def.value_type,
                description=score_def.desc,
                params={"aggregator": score_def.allele_aggregator},
            )
        return attributes

    @classmethod
    def _build_cnv_filter_func(
        cls, tree: Tree,
    ) -> Callable[[CNV], bool]:
        if tree.data == "and_":
            assert isinstance(tree.children[0], Tree)
            assert isinstance(tree.children[1], Tree)
            left_func = cls._build_cnv_filter_func(tree.children[0])
            right_func = cls._build_cnv_filter_func(tree.children[1])
            return lambda cnv: left_func(cnv) and right_func(cnv)
        if tree.data == "or":
            left_func = cls._build_cnv_filter_func(tree.children[0])
            right_func = cls._build_cnv_filter_func(tree.children[1])
            return lambda cnv: left_func(cnv) or right_func(cnv)

        left = tree.children[0]
        assert isinstance(left, Tree)
        assert isinstance(left.data, Token)
        left_type = left.data.value
        if left_type == "variable":
            assert isinstance(left.children[0], Tree)
            assert isinstance(left.children[0].data, Token)
            assert left.children[0].data.value == "word"
            assert isinstance(left.children[0].children[0], Token)
            left_value = left.children[0].children[0].value

            def left_accessor(_cnv: CNV) -> Any:
                return _cnv.attributes.get(left_value)
        else:
            assert isinstance(left.children[0], Tree)
            assert isinstance(left.children[0].data, Token)
            is_number = left.children[0].data.value == "number"
            assert isinstance(left.children[0].children[0], Token)
            left_value = left.children[0].children[0].value
            if is_number:
                left_value = float(left_value)

            def left_accessor(
                    _cnv: CNV) -> Any:  # pylint: disable=unused-argument
                return left_value
        assert isinstance(tree.children[1], Tree)
        assert isinstance(tree.children[1].children[0], Tree)
        assert isinstance(tree.children[1].children[0].data, Token)
        operator = tree.children[1].children[0].data.value
        right = tree.children[2]
        assert isinstance(right, Tree)
        assert isinstance(right.data, Token)
        right_type = right.data.value
        if right_type == "variable":
            assert isinstance(right.children[0], Tree)
            assert isinstance(right.children[0].data, Token)
            assert right.children[0].data.value == "word"
            assert isinstance(right.children[0].children[0], Token)
            right_value = right.children[0].children[0].value

            def right_accessor(_cnv: CNV) -> Any:
                return _cnv.attributes.get(right_value)
        else:
            assert isinstance(right.children[0], Tree)
            assert isinstance(right.children[0].data, Token)
            is_number = right.children[0].data.value == "number"
            assert isinstance(right.children[0].children[0], Token)
            right_value = right.children[0].children[0].value
            if is_number:
                right_value = float(right_value)

            def right_accessor(
                    _cnv: CNV) -> Any:  # pylint: disable=unused-argument
                return right_value

        if operator == "equals":
            return lambda cnv: left_accessor(cnv) == right_accessor(cnv)
        if operator == "greater_than":
            return lambda cnv: left_accessor(cnv) > right_accessor(cnv)
        if operator == "less_than":
            return lambda cnv: left_accessor(cnv) < right_accessor(cnv)
        if operator == "in":
            return lambda cnv: left_accessor(cnv) in right_accessor(cnv)

        raise ValueError(f"Unsupported operator {operator.data}")

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

        aggregators = {
            name: build_aggregator(aggregator)
            for name, (_, aggregator)
            in self.cnv_attributes.items()
            if aggregator is not None
        }

        for cnv in cnvs:
            for name, (attribute, _) in self.cnv_attributes.items():
                if name not in aggregators:
                    continue
                assert attribute.name is not None
                aggregators[name].add(cnv.attributes[attribute.name])

        ret = {}
        for attribute_config in self._info.attributes:
            if attribute_config.name in aggregators:
                ret[attribute_config.name] = \
                    aggregators[attribute_config.name].get_final()
            else:
                ret[attribute_config.name] = len(cnvs)

        return ret
