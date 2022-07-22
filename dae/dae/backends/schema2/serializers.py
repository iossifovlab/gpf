import functools
import operator
import logging

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

    SUMMARY_SEARCHABLE_PROPERTIES_TYPES = {
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
    }

    FAMILY_SEARCHABLE_PROPERTIES_TYPES = {
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

    PRODUCT_PROPERTIES_LIST = ["effect_gene", "allele_in_members"]

    BASE_SEARCHABLE_PROPERTIES_TYPES = {
        "bucket_index": pa.int32(),
        "chromosome": pa.string(),
        "position": pa.int32(),
        "end_position": pa.int32(),
        "effect_gene": pa.list_(
            pa.struct(
                [
                    pa.field("effect_gene_symbols", pa.string()),
                    pa.field("effect_types", pa.string()),
                ]
            )
        ),
        "summary_index": pa.int32(),
        "allele_index": pa.int32(),
        "variant_type": pa.int8(),
        "transmission_type": pa.int8(),
        "reference": pa.string(),
        "family_index": pa.int32(),
        "family_id": pa.string(),
        "is_denovo": pa.int8(),
        "allele_in_sexes": pa.int8(),
        "allele_in_statuses": pa.int8(),
        "allele_in_roles": pa.int32(),
        "inheritance_in_members": pa.int16(),
        "allele_in_members": pa.string(),
    }

    LIST_TO_ROW_PROPERTIES_LISTS = [["effect_gene"], ["allele_in_members"]]

    ENUM_PROPERTIES = {
        "variant_type": Allele.Type,
        "transmission_type": TransmissionType,
        "allele_in_sexes": Sex,
        "allele_in_roles": Role,
        "allele_in_statuses": Status,
        "inheritance_in_members": Inheritance,
    }

    GENOMIC_SCORES_SCHEMA_CLEAN_UP = [
        "worst_effect",
        "family_bin",
        "rare",
        "genomic_scores_data",
        "frequency_bin",
        "coding",
        "position_bin",
        "chrome_bin",
        "coding2",
        "region_bin",
        "coding_bin",
        "effect_data",
        "genotype_data",
        "inheritance_data",
        "genomic_scores_data",
        "variant_sexes",
        "alternatives_data",
        "chrom",
        "best_state_data",
        "summary_variant_index",
        "effect_type",
        "effect_gene",
        "variant_inheritance",
        "allele_in_member",
        "variant_roles",
        "genetic_model_data",
        "frequency_data",
        "alternative",
        "variant_data",
        "family_variant_index",
    ]

    def __init__(self, annotation_schema, extra_attributes=None):
        self.annotation_schema = annotation_schema
        self._schema_summary = None
        self._schema_family = None

        additional_searchable_props = {}
        scores_searchable = {}
        scores_binary = {}

        self.scores_serializers = scores_binary

        self.searchable_properties_summary_types = {
            **self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES,
            **additional_searchable_props,
            **scores_searchable,
        }

        self.searchable_properties_family_types = {
            **self.FAMILY_SEARCHABLE_PROPERTIES_TYPES
        }

        self.searchable_properties_types = {
            **self.BASE_SEARCHABLE_PROPERTIES_TYPES,
            **additional_searchable_props,
            **scores_searchable,
        }

        self.extra_attributes = []
        if extra_attributes:
            for attribute_name in extra_attributes:
                self.extra_attributes.append(attribute_name)

    @property
    def schema_summary(self):
        if self._schema_summary is None:
            fields = [
                pa.field(spr, pat)
                for spr, pat in (
                    self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES.items()
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
        if self._schema_family is None:
            fields = []
            for spr in self.FAMILY_SEARCHABLE_PROPERTIES_TYPES:
                field = pa.field(
                    spr, self.FAMILY_SEARCHABLE_PROPERTIES_TYPES[spr]
                )
                fields.append(field)

            fields.append(pa.field("family_variant_data", pa.string()))
            self._schema_family = pa.schema(fields)
        return self._schema_family

    @property
    def searchable_properties_summary(self):
        return self.searchable_properties_summary_types.keys()

    @property
    def searchable_properties_family(self):
        return self.searchable_properties_family_types.keys()

    @property
    def searchable_properties(self):
        return self.searchable_properties_types.keys()

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

    def build_family_allele_batch_dict(self, allele, family_variant_data):
        family_header = []
        family_properties = []

        for spr in self.FAMILY_SEARCHABLE_PROPERTIES_TYPES:
            prop_value = self._get_searchable_prop_value(allele, spr)

            family_header.append(spr)
            family_properties.append(prop_value)

        allele_data = {name: [] for name in self.schema_family.names}
        for name, value in zip(family_header, family_properties):
            allele_data[name].append(value)

        allele_data["family_variant_data"] = [family_variant_data]
        return allele_data

    def build_summary_allele_batch_dict(self, allele, summary_variant_data):
        allele_data = {"summary_variant_data": [summary_variant_data]}

        for spr in self.SUMMARY_SEARCHABLE_PROPERTIES_TYPES:

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
            for a in self.annotation_schema.public_fields:
                allele_data[a] = [allele.get_attribute(a)]

        return allele_data
