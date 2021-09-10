import copy
from typing import Dict, Any
from collections import OrderedDict
from box import Box

import pyarrow as pa


class Schema(object):

    # New types only need to be added here.
    type_map: Dict[str, Any] = OrderedDict(
        [
            ("str", str),
            ("float", float),
            ("int", int),
            ("list(str)", str),
            ("list(float)", float),
            ("list(int)", int),
        ]
    )

    def __init__(self):
        self.columns = OrderedDict()

    @classmethod
    def produce_type(cls, type_name):
        assert type_name in cls.type_map
        return Box(
            {"type_name": type_name, "type_py": cls.type_map[type_name]},
            default_box=True,
            default_box_attr=None,
        )

    def create_column(self, col_name, col_type):
        if col_name not in self.columns:
            self.columns[col_name] = Schema.produce_type(col_type)

    def remove_column(self, col_name):
        if col_name in self.columns:
            del self.columns[col_name]

    def order_as(self, ordered_col_names):
        ordered_schema = Schema()
        for col in ordered_col_names:
            assert col in self.columns, [col, self.col_names]
            ordered_schema.columns[col] = self.columns[col]
        return ordered_schema

    @classmethod
    def from_dict(cls, schema_dict):
        new_schema = Schema()
        assert isinstance(schema_dict, dict)
        for col_type in cls.type_map.keys():
            if col_type not in schema_dict:
                # TODO Should this skip the faulty col_type
                # or exit with an error? (or just print out an error?)
                continue
            for col in schema_dict[col_type]:
                new_schema.create_column(col, col_type)
        return new_schema

    @staticmethod
    def merge_schemas(left, right):
        merged_schema = Schema()
        missing_columns = OrderedDict()
        for col_name, col_type in right.columns.items():
            if col_name in left.columns:
                left.columns[col_name] = col_type
            else:
                missing_columns[col_name] = col_type
        merged_schema.columns.update(left.columns)
        merged_schema.columns.update(missing_columns)
        return merged_schema

    @staticmethod
    def diff_schemas(left, right):
        result = copy.deepcopy(left)
        for key in right.columns:
            if key in result.columns:
                del result.columns[key]
        return result

    @property
    def names(self):
        return list(self.columns.keys())

    @property
    def col_names(self):
        return list(self.columns.keys())

    def __str__(self):
        ret_str = ""
        for col, col_type in self.columns.items():
            ret_str += "{} -> [{}]\n".format(col, col_type.type_py)
        return ret_str

    def __contains__(self, key):
        return key in self.columns

    def __delitem__(self, key):
        del self.columns[key]

    def __getitem__(self, key):
        return self.columns.__getitem__(key)


class ParquetSchema(Schema):

    BASE_SCHEMA_FIELDS = [
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
    ]

    # New types only need to be added here.
    type_map: Dict[str, Any] = OrderedDict(
        [
            ("str", (str, pa.string())),
            ("float", (float, pa.float32())),
            ("float32", (float, pa.float32())),
            ("float64", (float, pa.float64())),
            ("int", (int, pa.uint32())),
            ("int8", (int, pa.int8())),
            ("tinyint", (int, pa.int8())),
            ("int16", (int, pa.int16())),
            ("smallint", (int, pa.int16())),
            ("int32", (int, pa.int32())),
            ("int64", (int, pa.int64())),
            ("bigint", (int, pa.int64())),
            ("list(str)", (str, pa.list_(pa.string()))),
            ("list(float)", (float, pa.list_(pa.float64()))),
            ("list(int)", (int, pa.list_(pa.uint32()))),
            ("bool", (bool, pa.bool_())),
            ("boolean", (bool, pa.bool_())),
            ("binary", (bytes, pa.binary())),
            ("string", (bytes, pa.string())),
        ]
    )

    def __init__(self, schema_dict={}):
        super(ParquetSchema, self).__init__()
        self.columns = {
            key: ParquetSchema.produce_type(val)
            for key, val in schema_dict.items()
        }

    @classmethod
    def produce_type(cls, type_name):
        assert type_name in cls.type_map, type_name
        return Box(
            {
                "type_name": type_name,
                "type_py": cls.type_map[type_name][0],
                "type_pa": cls.type_map[type_name][1],
                "type": cls.type_map[type_name][1],
            },
            default_box=True,
            default_box_attr=None,
        )

    def create_column(self, col_name, col_type):
        if col_name not in self.columns:
            self.columns[col_name] = ParquetSchema.produce_type(col_type)

    @classmethod
    def convert(cls, schema):
        if isinstance(schema, ParquetSchema):
            return schema
        assert isinstance(schema, Schema)
        pq_schema = ParquetSchema()
        for col_name, col_type in schema.columns.items():
            pq_schema.columns[col_name] = ParquetSchema.produce_type(
                col_type.type_name
            )
        return pq_schema

    @classmethod
    def from_dict(cls, schema_dict):
        return cls.convert(Schema.from_dict(schema_dict))

    @classmethod
    def merge_schemas(cls, left, right):
        return cls.convert(Schema.merge_schemas(left, right))

    @classmethod
    def from_parquet(cls, pq_schema):
        return cls.from_arrow(pq_schema.to_arrow_schema())

    @classmethod
    def from_arrow(cls, pa_schema):
        new_schema = ParquetSchema()
        for col in pa_schema:
            found = False
            for type_name, types in new_schema.type_map.items():
                if col.type == types[1]:
                    new_schema.columns[col.name] = cls.produce_type(type_name)
                    found = True
                    break
            assert found, col

        assert len(new_schema.columns) == len(pa_schema)
        return new_schema

    def to_arrow(self):
        return pa.schema(
            [
                pa.field(col, col_type.type_pa, nullable=True)
                for col, col_type in self.columns.items()
            ]
        )

    @classmethod
    def produce_base_schema(cls):
        return cls.from_arrow(pa.schema(cls.BASE_SCHEMA_FIELDS))

    def __str__(self):
        ret_str = ""
        for col, col_type in self.columns.items():
            ret_str += "{} -> [{} / {}]\n".format(
                col, col_type.type_py, col_type.type_pa
            )
        return ret_str
