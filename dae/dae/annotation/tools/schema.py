from __future__ import annotations

import logging

from typing import Dict, Any, Type, Optional
import pyarrow as pa

logger = logging.getLogger(__name__)


class Field:
    class Source:
        def __init__(
                self, annotator_type: str, resource_id: str, source_attr: str):
            self.annotator_type = annotator_type
            self.resource_id = resource_id
            self.source_attr = source_attr

    def __init__(
            self, name: str,
            py_type: Type, pa_type: Any = None,
            source: Optional[Field.Source] = None):

        self.name: str = name
        self.type: Type = py_type
        self.pa_type: Any = pa_type
        self.source: Optional[Field.Source] = source


class Schema:

    # New types only need to be added here.
    TYPE_MAP: Dict[str, Any] = {
        "str": (str, pa.string()),
        "float": (float, pa.float32()),
        "float32": (float, pa.float32()),
        "float64": (float, pa.float64()),
        "int": (int, pa.int32()),
        "int8": (int, pa.int8()),
        "tinyint": (int, pa.int8()),
        "int16": (int, pa.int16()),
        "smallint": (int, pa.int16()),
        "int32": (int, pa.int32()),
        "int64": (int, pa.int64()),
        "bigint": (int, pa.int64()),
        "list(str)": (list, pa.list_(pa.string())),
        "list(float)": (list, pa.list_(pa.float64())),
        "list(int)": (list, pa.list_(pa.int32())),
        "bool": (bool, pa.bool_()),
        "boolean": (bool, pa.bool_()),
        "binary": (bytes, pa.binary()),
        "string": (bytes, pa.string()),
    }

    def __init__(self):
        self.fields: Dict[str, Field] = {}

    def create_field(
            self, name: str, py_type: Type, pa_type: Any = None,
            annotator_type: str = None, resource_id: str = None,
            source_attr: str = None):
        if name not in self.fields:
            source = None
            if annotator_type or resource_id or source_attr:
                source = Field.Source(annotator_type, resource_id, source_attr)
            self.fields[name] = Field(name, py_type, pa_type, source)

    @staticmethod
    def merge_schemas(left: Schema, right: Schema) -> Schema:
        merged_schema = Schema()
        missing_fields = {}
        for field_name, field in right.fields.items():
            if field_name in left.fields:
                left.fields[field_name] = field
            else:
                missing_fields[field_name] = field
        merged_schema.fields.update(left.fields)
        merged_schema.fields.update(missing_fields)
        return merged_schema

    @staticmethod
    def concat_schemas(first: Schema, second: Schema) -> Schema:
        result = Schema()
        result.fields.update(first.fields)

        for name, field in second.fields.items():
            if name in result:
                message = f"two schemas has fields with the same name: " \
                    f"first {first[name]}; second {field}"
                logger.error(message)
                raise ValueError(message)
            result.fields[name] = field

        return result

    @property
    def names(self):
        return list(self.fields.keys())

    def __str__(self):
        ret_str = ""
        for field_name, field in self.fields.items():
            ret_str += "{} -> [{}]\n".format(field_name, field.type)
        return ret_str

    def __contains__(self, key):
        return key in self.fields

    def __delitem__(self, key):
        del self.fields[key]

    def __getitem__(self, key):
        return self.fields.__getitem__(key)

    def __len__(self):
        return len(self.fields)

    BASE_SCHEMA = pa.schema([
        pa.field("bucket_index", pa.int32()),
        pa.field("summary_variant_index", pa.int64()),
        pa.field("allele_index", pa.int8()),
        pa.field("chrom", pa.string()),
        pa.field("position", pa.int32()),
        pa.field("end_position", pa.int32()),
        pa.field("reference", pa.string()),
        pa.field("alternative", pa.string()),
        pa.field("variant_type", pa.int8()),
        pa.field("transmission_type", pa.int8()),
        # pa.field("worst_effect", pa.string()),
        pa.field("alternatives_data", pa.string()),
        pa.field("effect_type", pa.string()),
        pa.field("effect_gene", pa.string()),
        pa.field("effect_data", pa.string()),
        pa.field("family_variant_index", pa.int64()),
        pa.field("family_id", pa.string()),
        pa.field("is_denovo", pa.bool_()),
        pa.field("variant_sexes", pa.int8()),
        pa.field("variant_roles", pa.int32()),
        pa.field("variant_inheritance", pa.int16()),
        pa.field("variant_in_member", pa.string()),
        pa.field("genotype_data", pa.string()),
        pa.field("best_state_data", pa.string()),
        pa.field("genetic_model_data", pa.int8()),
        pa.field("inheritance_data", pa.string()),
        pa.field("af_parents_called_count", pa.int32()),
        pa.field("af_parents_called_percent", pa.float32()),
        pa.field("af_allele_count", pa.int32()),
        pa.field("af_allele_freq", pa.float32()),
        pa.field("frequency_data", pa.string()),
        pa.field("genomic_scores_data", pa.string()),
    ])

    @classmethod
    def produce_base_schema(cls):
        return cls.from_arrow_schema(cls.BASE_SCHEMA)

    @classmethod
    def from_impala_schema(cls, schema_dict):
        new_schema = Schema()
        for name, type_name in schema_dict.items():
            py_type, pa_type = cls.TYPE_MAP[type_name]
            field = Field(name, py_type, pa_type)
            new_schema.fields[name] = field
        return new_schema

    @classmethod
    def from_arrow_schema(cls, pa_schema: pa.Schema):
        new_schema = Schema()
        for col in pa_schema:
            found = False
            for py_type, pa_type in cls.TYPE_MAP.values():
                if col.type == pa_type:
                    new_schema.fields[col.name] = \
                        Field(col.name, py_type, pa_type)
                    found = True
                    break
            assert found, col

        assert len(new_schema.fields) == len(pa_schema)
        return new_schema
