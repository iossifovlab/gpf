import functools
import operator
import logging
from typing import Any

import pyarrow as pa
from dae.variants.core import Allele
from dae.variants.attributes import (
    Inheritance,
    TransmissionType,
    Sex,
    Role,
    Status,
)

logger = logging.getLogger(__name__)


class AlleleParquetSerializer:
    """Serialize a bunch of alleles."""

    SUMMARY_ALLELE_BASE_SCHEMA = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        "effect_gene": pa.list_(
            pa.field(
                "element",
                pa.struct(
                    [
                        pa.field("effect_gene_symbols", pa.string()),
                        pa.field("effect_types", pa.string()),
                    ]
                ),
            )
        ),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
        "af_allele_count": pa.int32(),
        "af_allele_freq": pa.float32(),
        "af_parents_called": pa.int32(),
        "af_parents_freq": pa.float32(),
        "seen_as_denovo": pa.bool_(),
        "seen_in_status": pa.int8(),
        "family_variants_count": pa.int32(),
        "family_alleles_count": pa.int32(),
    }

    FAMILY_ALLELE_BASE_SCHEMA = {
        "bucket_index": pa.int32(),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "allele_in_sexes": pa.int8(),
        "allele_in_statuses": pa.int8(),
        "allele_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "allele_in_members": pa.list_(pa.string()),
    }

    ENUM_PROPERTIES = {
        "variant_type": Allele.Type,
        "transmission_type": TransmissionType,
        "allele_in_sexes": Sex,
        "allele_in_roles": Role,
        "allele_in_statuses": Status,
        "inheritance_in_members": Inheritance,
    }

    def __init__(self, annotation_schema, extra_attributes=None):
        self.annotation_schema = annotation_schema
        self._schema_summary = None
        self._schema_family = None

        self.extra_attributes = []
        if extra_attributes:
            for attribute_name in extra_attributes:
                self.extra_attributes.append(attribute_name)

    @property
    def schema_summary(self):
        """Lazy construct and return the schema for the summary alleles."""
        if self._schema_summary is None:
            fields = [
                pa.field(spr, pat)
                for spr, pat in (
                    self.SUMMARY_ALLELE_BASE_SCHEMA.items()
                )
            ]
            fields.append(pa.field("summary_variant_data", pa.string()))

            annotation_type_to_pa_type = {
                "float": pa.float32(),
                "int": pa.int32(),
            }

            if self.annotation_schema is not None:
                for annotation in self.annotation_schema.public_fields:
                    annotation_field_type = self.annotation_schema[
                        annotation
                    ].type

                    if annotation_field_type in annotation_type_to_pa_type:
                        fields.append(
                            pa.field(
                                annotation,
                                annotation_type_to_pa_type[
                                    annotation_field_type
                                ],
                            )
                        )

            self._schema_summary = pa.schema(fields)
        return self._schema_summary

    @property
    def schema_family(self):
        """Lazy construct and return the schema for the family alleles."""
        if self._schema_family is None:
            fields = []
            for spr, ftype in self.FAMILY_ALLELE_BASE_SCHEMA.items():
                field = pa.field(spr, ftype)
                fields.append(field)

            fields.append(pa.field("family_variant_data", pa.string()))
            self._schema_family = pa.schema(fields)
        return self._schema_family

    def _get_searchable_prop_value(self, allele, spr):
        prop_value = getattr(allele, spr, None)
        if prop_value is None:
            prop_value = allele.get_attribute(spr)
        if prop_value and spr in self.ENUM_PROPERTIES:
            if isinstance(prop_value, list):
                prop_value = functools.reduce(
                    operator.or_,
                    [enum.value for enum in prop_value if enum is not None],
                    0,
                )
            else:
                prop_value = prop_value.value
        return prop_value

    def build_family_allele_batch_dict(self, allele, family_variant_data) \
            -> dict[str, list[Any]]:
        """Build a batch of family allele data in the form of a dict."""
        family_header = []
        family_properties = []

        for spr in self.FAMILY_ALLELE_BASE_SCHEMA:
            prop_value = self._get_searchable_prop_value(allele, spr)

            family_header.append(spr)
            family_properties.append(prop_value)

        allele_data: dict[str, list] = {
            name: [] for name in self.schema_family.names
        }
        for name, value in zip(family_header, family_properties):
            allele_data[name].append(value)

        allele_data["family_variant_data"] = [family_variant_data]
        return allele_data

    def build_summary_allele_batch_dict(self, allele, summary_variant_data) \
            -> dict[str, list[Any]]:
        """Build a batch of summary allele data in the form of a dict."""
        allele_data = {"summary_variant_data": [summary_variant_data]}

        for spr in self.SUMMARY_ALLELE_BASE_SCHEMA:

            if spr == "effect_gene":
                if allele.effect_types is None:
                    assert allele.effect_gene_symbols is None
                    prop_value = [
                        {"effect_types": None, "effect_gene_symbols": None}
                    ]
                else:
                    prop_value = [
                        {"effect_types": e[0], "effect_gene_symbols": e[1]}
                        for e in zip(
                            allele.effect_types, allele.effect_gene_symbols
                        )
                    ]
            else:
                prop_value = self._get_searchable_prop_value(allele, spr)

            allele_data[spr] = [prop_value]

        if self.annotation_schema is not None:
            for field in self.annotation_schema.public_fields:
                allele_data[field] = [allele.get_attribute(field)]

        return allele_data
