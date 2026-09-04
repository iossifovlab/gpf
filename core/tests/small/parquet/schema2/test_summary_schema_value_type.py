"""Regression (#949): summary-parquet storage keys on the raw declared
(spec) value type, not the post-aggregation type.

A ``str`` genomic score defaults to the ``list`` position/allele
aggregator (``ListAggregator.output_value_type == "list"``). Two coupled
sites must therefore look at the spec type, not the aggregated type:

* ``build_summary_schema`` -- keying the column on ``"list"`` drops it
  (not a scalar parquet type), so score-filter queries later fail with
  ``Binder Error: Table "sa" does not have a column named "CLNSIG"`` and
  return zero variants.
* the annotation stringify gate -- a ``list`` value must be stringified
  into the ``pa.string()`` column the schema reserves for it.

If only one of the two is changed, a list value clashes with its column,
so both are tested here together.

The fixtures NAME their aggregator rather than holding an instance,
because a name is all an ``Attribute`` carries since gain#1133 (gpf#1013).
What bites here is therefore gain resolving the class from that name --
which CI does, running against the latest green gain master.  Against an
older gain, one that read the output type off a held
``aggregator_instance``, ``get_value_type(aggregated=True)`` falls back to
the spec type and a regression to ``aggregated=True`` slips past all
three tests: locally, update gain before trusting them.
"""
from types import SimpleNamespace

import pyarrow as pa
from gain.annotation.annotate_utils import stringify
from gain.annotation.annotation_config import Attribute
from gain.annotation.annotation_pipeline import AttributeSpec

from gpf.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsFilterMixin,
)
from gpf.parquet.schema2.serializers import build_summary_schema


def _attr(value_type: str, aggregator: str) -> Attribute:
    """An attribute declaring ``value_type``, aggregated by ``aggregator``.

    The aggregator is named, not instantiated: since gain#1133 an
    ``Attribute`` carries its aggregator's name and resolves the class
    from it, and the ``aggregator_instance`` field these fixtures used to
    pass is gone.
    """
    return Attribute(
        "score", "SCORE", internal=False,
        aggregator=aggregator,
        spec=AttributeSpec(
            source="SCORE", value_type=value_type,
            description="", internal_default=False),
    )


def test_str_score_with_list_aggregator_is_kept_as_string_column() -> None:
    # ListAggregator.output_value_type == "list"; keying on that drops the
    # column. The spec type "str" must win -> pa.string().
    schema = build_summary_schema([_attr("str", "list")])

    assert "score" in schema.names
    assert schema.field("score").type == pa.string()


def test_score_column_keys_on_spec_type_not_aggregator_output() -> None:
    # MeanAggregator.output_value_type == "float". The column must follow
    # the declared spec type ("int" -> int32), locking in aggregated=False;
    # a regression to aggregated=True would type this column as float32
    # -- on a gain that resolves the class from the name, see module docs.
    schema = build_summary_schema([_attr("int", "mean")])

    assert schema.field("score").type == pa.int32()


class _OneAttrPipeline:
    """Minimal annotation-pipeline stand-in exposing only what the
    variants filter mixin reads: the attribute set and per-key lookup."""

    def __init__(self, attr: Attribute) -> None:
        self._attr = attr

    def get_attributes(self) -> list[Attribute]:
        return [self._attr]

    def get_attribute_info(self, key: str) -> Attribute | None:
        return self._attr if key == self._attr.name else None


class _RecordingAllele:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def update_attributes(self, attributes: dict[str, object]) -> None:
        self.attributes.update(attributes)


def test_list_value_for_str_score_is_stringified_for_storage() -> None:
    # The coupled half: a str-typed score whose aggregated value is a list
    # must be stringified, so it fits the pa.string() column the schema
    # reserves. Driven by the spec type ("str"), not get_value_type()
    # ("list") -- otherwise the raw list would clash with the column.
    attr = _attr("str", "list")
    flt = AnnotationPipelineVariantsFilterMixin(_OneAttrPipeline(attr))
    allele = _RecordingAllele()
    annotation = SimpleNamespace(context={"score": ["Pathogenic", "Benign"]})

    flt._apply_annotation_to_allele(allele, annotation)

    stored = allele.attributes["score"]
    assert isinstance(stored, str)
    assert stored == stringify(["Pathogenic", "Benign"])
